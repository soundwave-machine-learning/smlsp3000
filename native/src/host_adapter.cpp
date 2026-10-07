#include "smlsp3000/host_adapter.hpp"
#include "track_a_assets_v1.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>

namespace smlsp3000 {
namespace A = assets_v1;

double HostAdapter::clamp_parameter(ParamId id, double v) {
    if (!std::isfinite(v)) return 0.0;
    switch (id) {
        case ParamId::SP_INPUT_LEVEL_DB: return std::clamp(v, A::CTRL_SP_INPUT_LEVEL_DB_MIN, A::CTRL_SP_INPUT_LEVEL_DB_MAX);
        case ParamId::SP_INPUT_GAIN_DB: { double best = 0.0, bd = 1e300; for (int s : A::SP_INPUT_GAIN_STEPS_DB) { const double d = std::fabs(v - s); if (d < bd) { bd = d; best = s; } } return best; }
        case ParamId::INTERSTAGE_LEVEL_DB: return std::clamp(v, A::PRODUCT_INTERSTAGE_RESEARCH_MIN_DB, A::PRODUCT_INTERSTAGE_RESEARCH_MAX_DB);
        case ParamId::MPC_INPUT_GAIN: return std::clamp(std::round(v), 0.0, 2.0);
        case ParamId::OUTPUT_TRIM_DB: return std::clamp(v, A::CTRL_OUTPUT_TRIM_DB_MIN, A::CTRL_OUTPUT_TRIM_DB_MAX);
        default: return v != 0.0 ? 1.0 : 0.0;
    }
}

PrepareResult HostAdapter::prepare(int host_rate, std::size_t max_block, const ProductParameters& initial, const ResearchConfiguration* research) {
    prepared_ = false;
    ProductParameters p = initial; p.plugin_bypass = false;        // the adapter owns bypass; the core never switches its own dry path
    auto r = engine_.prepare(host_rate, ADAPTER_CHANNELS, max_block, p, research);
    if (!r.ok) return r;
    host_rate_ = host_rate; max_block_ = max_block;
    const double vals[6] = {p.sp_input_level_db, static_cast<double>(p.sp_input_gain_db), p.interstage_level_db, static_cast<double>(static_cast<int>(p.mpc_input_gain)), p.output_trim_db, initial.plugin_bypass ? 1.0 : 0.0};
    for (int i = 0; i < 6; ++i) { targets_[static_cast<std::size_t>(i)].store(vals[i]); applied_[static_cast<std::size_t>(i)] = vals[i]; }
    pending_slot_.store(-1);
    dry_.assign(ADAPTER_CHANNELS, DelayLine());
    for (auto& d : dry_) d.prepare(static_cast<std::size_t>(engine_.latency()), max_block);
    dbuf_.assign(max_block, 0.0);
    for (int c = 0; c < 2; ++c) { in64_[c].assign(max_block, 0.0); out64_[c].assign(max_block, 0.0); sbuf_[c].assign(max_block, 0.0); }
    inp_.assign(ADAPTER_CHANNELS, nullptr); outp_.assign(ADAPTER_CHANNELS, nullptr);
    w_step_ = 1.0 / (BYPASS_CROSSFADE_MS / 1000.0 * host_rate);
    prepared_ = true;
    reset();
    return r;
}

void HostAdapter::reset() {
    if (!prepared_) return;
    ProductParameters p = engine_.product();                     // stream start: the current targets become the configured values (no ramp from stale values)
    p.sp_input_level_db = targets_[0].load(); p.sp_input_gain_db = static_cast<int>(targets_[1].load()); p.interstage_level_db = targets_[2].load();
    p.mpc_input_gain = static_cast<MpcInputGain>(static_cast<int>(targets_[3].load())); p.output_trim_db = targets_[4].load(); p.plugin_bypass = false;
    engine_.update_product_targets(p);
    for (int i = 0; i < 5; ++i) applied_[static_cast<std::size_t>(i)] = targets_[static_cast<std::size_t>(i)].load();
    engine_.reset();
    for (auto& d : dry_) d.reset();
    w_ = targets_[5].load() != 0.0 ? 0.0 : 1.0;                   // snap to the current bypass target (startup/reset in bypass → fully dry)
    applied_[5] = targets_[5].load();
    for (int c = 0; c < 2; ++c) { const auto ci = static_cast<std::size_t>(c); m_in_[ci].store(0.0); m_mpc_[ci].store(0.0); m_out_[ci].store(0.0); m_in_hold_[ci].store(0.0); m_out_hold_[ci].store(0.0); m_sp_clip_[ci].store(0); m_c18_[ci].store(0); m_c16_[ci].store(0); m_over_[ci].store(false); }
    m_nonfinite_.store(0); m_faults_.store(0); m_rejected_.store(0); m_blocks_.store(0); m_fault_.store(false); m_w_.store(w_);
}

void HostAdapter::set_parameter(ParamId id, double value) { targets_[static_cast<std::size_t>(static_cast<int>(id))].store(clamp_parameter(id, value), std::memory_order_relaxed); }

StateLoadResult HostAdapter::load_state(std::string_view text) {
    ProductParameters p = ProductParameters::defaults();
    auto r = Engine::parse_state(text, p);
    if (!r.ok) return r;                                          // nothing applied on rejection
    set_parameter(ParamId::SP_INPUT_LEVEL_DB, p.sp_input_level_db); set_parameter(ParamId::SP_INPUT_GAIN_DB, p.sp_input_gain_db);
    set_parameter(ParamId::INTERSTAGE_LEVEL_DB, p.interstage_level_db); set_parameter(ParamId::MPC_INPUT_GAIN, static_cast<double>(static_cast<int>(p.mpc_input_gain)));
    set_parameter(ParamId::OUTPUT_TRIM_DB, p.output_trim_db); set_parameter(ParamId::PLUGIN_BYPASS, p.plugin_bypass ? 1.0 : 0.0);
    slots_[static_cast<std::size_t>(writer_slot_)] = p;           // publish the validated record (the audio thread applies it as events)
    pending_slot_.store(writer_slot_, std::memory_order_release); writer_slot_ ^= 1;
    return r;
}

std::string HostAdapter::save_state() const {
    Engine tmp;                                                   // message thread: build the record from the current targets through the core's serializer
    ProductParameters p = ProductParameters::defaults();
    p.sp_input_level_db = targets_[0].load(); p.sp_input_gain_db = static_cast<int>(targets_[1].load()); p.interstage_level_db = targets_[2].load();
    p.mpc_input_gain = static_cast<MpcInputGain>(static_cast<int>(targets_[3].load())); p.output_trim_db = targets_[4].load();
    // serialisation needs no prepared engine: use a lightweight path through parse/serialize symmetry
    std::string s;
    s += "smlsp3000-state\n";
    s += "schema_version=" + std::to_string(A::CONTROLS_SCHEMA_VERSION) + "\n";
    s += std::string("controls=") + A::CONTROLS_ID + ";" + A::CONTROLS_SHA256 + "\n";
    s += std::string("product_config=") + A::PRODUCT_CONFIG_ID + ";" + A::PRODUCT_CONFIG_VERSION + ";" + A::PRODUCT_CONFIG_SHA256 + "\n";
    s += std::string("sp_asset=") + A::SP_ASSET_ID + ";" + A::SP_ASSET_VERSION + ";" + A::SP_MODEL_VERSION + ";" + A::SP_ASSET_SHA256 + "\n";
    s += std::string("mpc_asset=") + A::MPC_ASSET_ID + ";" + A::MPC_ASSET_VERSION + ";" + A::MPC_MODEL_VERSION + ";" + A::MPC_ASSET_SHA256 + "\n";
    char b[64];
    std::snprintf(b, sizeof b, "%.17g", p.sp_input_level_db); s += std::string("sp_input_level_db=") + b + "\n";
    s += "sp_input_gain_db=" + std::to_string(p.sp_input_gain_db) + "\n";
    std::snprintf(b, sizeof b, "%.17g", p.interstage_level_db); s += std::string("interstage_level_db=") + b + "\n";
    s += std::string("mpc_input_gain=") + mpc_gain_name(p.mpc_input_gain) + "\n";
    std::snprintf(b, sizeof b, "%.17g", p.output_trim_db); s += std::string("output_trim_db=") + b + "\n";
    s += std::string("plugin_bypass=") + (targets_[5].load() != 0.0 ? "1" : "0") + "\n";
    (void)tmp;
    return s;
}

void HostAdapter::apply_pending_and_events() {
    // a published state record only refreshes the targets (already done by load_state); consuming it here keeps the handoff explicit
    const int slot = pending_slot_.exchange(-1, std::memory_order_acquire); (void)slot;
}

void HostAdapter::process_chunk(const double* const* in, double* const* out, std::size_t n) {
    apply_pending_and_events();
    // block-boundary parameter delivery: every changed target becomes an event at offset 0 (the core ramps 10 ms; switches are discrete)
    ParamEvent ev[5]; std::size_t n_ev = 0;
    for (int i = 0; i < 5; ++i) {
        const double t = targets_[static_cast<std::size_t>(i)].load(std::memory_order_relaxed);
        if (t != applied_[static_cast<std::size_t>(i)]) { ev[n_ev++] = ParamEvent{static_cast<ParamId>(i), 0, t}; applied_[static_cast<std::size_t>(i)] = t; }
    }
    const double byp = targets_[5].load(std::memory_order_relaxed); applied_[5] = byp;
    // input policy (OWN-DEC-019/029): NaN/Inf samples become zero and are counted here, so that BOTH the core and the dry bypass path
    // see the same sanitised input (a NaN reaching the dry path would otherwise poison the crossfade sum)
    const double* clean[2];
    std::int64_t nonfinite = 0;
    for (int c = 0; c < ADAPTER_CHANNELS; ++c) {
        const auto ci = static_cast<std::size_t>(c); double* dst = sbuf_[c].data();
        for (std::size_t m = 0; m < n; ++m) { const double v = in[ci][m]; if (std::isfinite(v)) dst[m] = v; else { dst[m] = 0.0; ++nonfinite; } }
        clean[c] = dst;
    }
    engine_.reset_meters();                                        // per-block peaks; cumulative counts are accumulated below
    engine_.process(clean, out, n, n_ev ? ev : nullptr, n_ev);
    const Meters& em = engine_.meters();
    const double target_w = byp != 0.0 ? 0.0 : 1.0;
    for (int c = 0; c < ADAPTER_CHANNELS; ++c) {
        const auto ci = static_cast<std::size_t>(c);
        dry_[ci].process(clean[c], n, dbuf_.data());               // latency-aligned original (sanitised) input, before every gain
        double w = w_, opk = 0.0; bool over = false;
        for (std::size_t m = 0; m < n; ++m) {
            if (w != target_w) { w = target_w > w ? std::min(target_w, w + w_step_) : std::max(target_w, w - w_step_); }
            const double o = w * out[ci][m] + (1.0 - w) * dbuf_[m];
            out[ci][m] = o; const double a = std::fabs(o); if (a > opk) opk = a; if (a > 1.0) over = true;
        }
        if (c == ADAPTER_CHANNELS - 1) w_ = w;                     // both channels share the same weight trajectory
        double ipk = 0.0; for (std::size_t m = 0; m < n; ++m) { const double a = std::fabs(clean[c][m]); if (a > ipk) ipk = a; }
        m_in_[ci].store(ipk, std::memory_order_relaxed); m_out_[ci].store(opk, std::memory_order_relaxed); m_over_[ci].store(over, std::memory_order_relaxed);
        if (ipk > m_in_hold_[ci].load(std::memory_order_relaxed)) m_in_hold_[ci].store(ipk, std::memory_order_relaxed);
        if (opk > m_out_hold_[ci].load(std::memory_order_relaxed)) m_out_hold_[ci].store(opk, std::memory_order_relaxed);
        m_mpc_[ci].store(em.channel[ci].mpc_core_input_peak, std::memory_order_relaxed);
        m_sp_clip_[ci].fetch_add(em.channel[ci].sp_clip, std::memory_order_relaxed); m_c18_[ci].fetch_add(em.channel[ci].mpc_clip18, std::memory_order_relaxed); m_c16_[ci].fetch_add(em.channel[ci].mpc_clamp16, std::memory_order_relaxed);
    }
    m_nonfinite_.fetch_add(nonfinite + em.nonfinite_input_samples, std::memory_order_relaxed); m_faults_.fetch_add(em.faults, std::memory_order_relaxed); m_rejected_.fetch_add(em.events_rejected, std::memory_order_relaxed);
    if (em.fault_latched) m_fault_.store(true, std::memory_order_relaxed);
    m_w_.store(w_, std::memory_order_relaxed); m_blocks_.fetch_add(1, std::memory_order_relaxed);
}

void HostAdapter::process(const double* const* in, double* const* out, std::size_t frames) {
    if (!prepared_) { for (int c = 0; c < ADAPTER_CHANNELS; ++c) std::memset(out[c], 0, frames * sizeof(double)); return; }
    std::size_t done = 0;
    while (done < frames) {                                        // bounded internal chunking at the prepared maximum
        const std::size_t n = std::min(max_block_, frames - done);
        for (int c = 0; c < ADAPTER_CHANNELS; ++c) { inp_[static_cast<std::size_t>(c)] = in[c] + done; outp_[static_cast<std::size_t>(c)] = out[c] + done; }
        process_chunk(inp_.data(), outp_.data(), n);
        done += n;
    }
}

void HostAdapter::process(const float* const* in, float* const* out, std::size_t frames) {
    if (!prepared_) { for (int c = 0; c < ADAPTER_CHANNELS; ++c) std::memset(out[c], 0, frames * sizeof(float)); return; }
    std::size_t done = 0;
    while (done < frames) {
        const std::size_t n = std::min(max_block_, frames - done);
        for (int c = 0; c < ADAPTER_CHANNELS; ++c) {
            const float* src = in[c] + done; double* dst = in64_[c].data();
            for (std::size_t m = 0; m < n; ++m) dst[m] = static_cast<double>(src[m]);       // promotion (exact)
            inp_[static_cast<std::size_t>(c)] = dst; outp_[static_cast<std::size_t>(c)] = out64_[c].data();
        }
        process_chunk(inp_.data(), outp_.data(), n);
        for (int c = 0; c < ADAPTER_CHANNELS; ++c) { float* dst = out[c] + done; const double* src = out64_[c].data(); for (std::size_t m = 0; m < n; ++m) dst[m] = static_cast<float>(src[m]); }   // final cast
        done += n;
    }
}

MeterSnapshot HostAdapter::meters() const {
    MeterSnapshot s; s.prepared = prepared_; s.latency = latency(); s.host_rate = host_rate_;
    for (int c = 0; c < 2; ++c) { const auto ci = static_cast<std::size_t>(c);
        s.input_peak[c] = m_in_[ci].load(); s.mpc_core_input_peak[c] = m_mpc_[ci].load(); s.output_peak[c] = m_out_[ci].load(); s.input_peak_hold[c] = m_in_hold_[ci].load(); s.output_peak_hold[c] = m_out_hold_[ci].load();
        s.sp_clip[c] = m_sp_clip_[ci].load(); s.mpc_clip18[c] = m_c18_[ci].load(); s.mpc_clamp16[c] = m_c16_[ci].load(); s.output_over_range[c] = m_over_[ci].load(); }
    s.nonfinite_input_samples = m_nonfinite_.load(); s.faults = m_faults_.load(); s.events_rejected = m_rejected_.load(); s.blocks_processed = m_blocks_.load(); s.fault_latched = m_fault_.load(); s.bypass_weight = m_w_.load();
    return s;
}

void HostAdapter::reset_hold() { for (int c = 0; c < 2; ++c) { m_in_hold_[static_cast<std::size_t>(c)].store(0.0); m_out_hold_[static_cast<std::size_t>(c)].store(0.0); } }

}  // namespace smlsp3000
