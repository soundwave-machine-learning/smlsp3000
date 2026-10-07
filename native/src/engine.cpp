#include "smlsp3000/engine.hpp"
#include "smlsp3000/numerics.hpp"
#include "track_a_assets_v1.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace smlsp3000 {
namespace A = assets_v1;

static constexpr int SUPPORTED_RATES[6] = {44100, 48000, 88200, 96000, 176400, 192000};

const char* chain_mode_name(ChainMode m) {
    switch (m) { case ChainMode::CASCADE: return "CASCADE"; case ChainMode::SP_ONLY: return "SP_ONLY"; case ChainMode::MPC_ONLY: return "MPC_ONLY"; default: return "BOTH_MACHINE_BYPASSED"; }
}
const char* mpc_gain_name(MpcInputGain g) { return A::MPC_INPUT_GAIN_NAMES[static_cast<int>(g)]; }
bool parse_chain_mode(std::string_view s, ChainMode& out) {
    for (int i = 0; i < 4; ++i) if (s == chain_mode_name(static_cast<ChainMode>(i))) { out = static_cast<ChainMode>(i); return true; }
    return false;
}
bool parse_mpc_gain(std::string_view s, MpcInputGain& out) {
    for (int i = 0; i < 3; ++i) if (s == A::MPC_INPUT_GAIN_NAMES[i]) { out = static_cast<MpcInputGain>(i); return true; }
    return false;
}

ProductParameters ProductParameters::defaults() {
    ProductParameters p;
    p.sp_input_level_db = A::CTRL_SP_INPUT_LEVEL_DB_DEFAULT; p.sp_input_gain_db = A::CTRL_SP_INPUT_GAIN_DEFAULT_DB;
    p.interstage_level_db = A::CTRL_INTERSTAGE_LEVEL_DB_DEFAULT; parse_mpc_gain(A::CTRL_MPC_INPUT_GAIN_DEFAULT, p.mpc_input_gain);
    p.output_trim_db = A::CTRL_OUTPUT_TRIM_DB_DEFAULT; p.plugin_bypass = A::CTRL_PLUGIN_BYPASS_DEFAULT;
    parse_chain_mode(A::PRODUCT_CHAIN_MODE_DEFAULT, p.chain_mode); p.mpc_record_level_db = A::PROFILE_MPC_RECORD_LEVEL_DB_FIXED;
    p.sp_output_path = A::PRODUCT_SP_OUTPUT_PATH; p.mpc_output_route = A::PRODUCT_MPC_OUTPUT_ROUTE; p.physical_calibration = false;
    return p;
}

ResearchConfiguration ResearchConfiguration::checkpoint() {
    ResearchConfiguration r;
    r.quantizer_rule = std::string_view(A::SP_RC_QUANTIZER_RULE) == "FLOOR" ? QuantizerRule::FLOOR : QuantizerRule::ROUND_NEAREST;
    r.quantizer_offset_codes = A::SP_RC_QUANTIZER_OFFSET_CODES; r.quantizer_bypass = A::SP_RC_QUANTIZER_BYPASS;
    r.reduction_rule = std::string_view(A::MPC_RC_REDUCTION_RULE) == "TRUNCATION" ? ReductionRule::TRUNCATION : ReductionRule::ROUND_NEAREST;
    r.converter_quant_bypass = A::MPC_RC_QUANT_BYPASS;
    r.proxy_oversampling = A::SP_RC_PROXY_OVERSAMPLING; r.lobes = A::SP_RC_LOBES_PER_SIDE; r.lp_beta = A::SP_RC_LOWPASS_KAISER_BETA;
    r.sp_hw_s_host = A::SP_RC_SAMPLER_HALF_WIDTH_HOST; r.sp_hw_z_host = A::SP_RC_HOLD_KERNEL_HALF_WIDTH_HOST; r.sp_interp_beta = A::SP_RC_INTERP_KAISER_BETA;
    r.r12_half_host = A::MPC_RC_R12_HALF_WIDTH_HOST; r.r12_beta = A::MPC_RC_R12_KAISER_BETA; r.mpc_hw_s_host = A::MPC_RC_SAMPLER_HALF_WIDTH_HOST;
    r.hw_r = A::MPC_RC_RECON_HALF_WIDTH_MACHINE; r.mpc_interp_beta = A::MPC_RC_INTERP_KAISER_BETA;
    r.slot_skew_enabled = A::SP_RC_SLOT_SKEW_ENABLED; r.capture_offset_enabled = A::SP_RC_CAPTURE_OFFSET_ENABLED; r.reverse_order_research = A::CASCADE_RC_REVERSE_ORDER_RESEARCH;
    return r;
}

// ---------------------------------------------------------------- ramps and switches
static double db_to_gain(double db) { return std::pow(10.0, db / 20.0); }   // same formula as the reference (10.0 ** (db / 20.0))

void GainRamp::configure(double initial_db, std::int64_t ramp_len) { ramp_len_ = ramp_len; reset(initial_db); }
void GainRamp::reset(double initial_db) { target_db_ = cur_db_ = initial_db; step_db_ = 0.0; remaining_ = 0; gain_ = gain_of(initial_db); clock_ = 0; pending_n_ = 0; }
bool GainRamp::schedule(std::int64_t at, double target_db) {
    if (pending_n_ >= static_cast<int>(pending_.size())) return false;
    int i = pending_n_++;                                            // keep sorted by `at` (stable for equal times: later event wins later)
    while (i > 0 && pending_[static_cast<std::size_t>(i - 1)].at > at) { pending_[static_cast<std::size_t>(i)] = pending_[static_cast<std::size_t>(i - 1)]; --i; }
    pending_[static_cast<std::size_t>(i)] = {at, target_db};
    return true;
}
void GainRamp::start(double target_db) {
    if (target_db == target_db_ && (remaining_ > 0 || cur_db_ == target_db_)) return;   // redundant retarget: keep the running trajectory (no restart)
    target_db_ = target_db;
    if (ramp_len_ <= 0 || cur_db_ == target_db_) { cur_db_ = target_db_; remaining_ = 0; gain_ = gain_of(cur_db_); return; }
    step_db_ = (target_db_ - cur_db_) / static_cast<double>(ramp_len_); remaining_ = ramp_len_;   // continues from the current smoothed value
}
double GainRamp::gain_of(double db) const { return db_to_gain(db); }
double GainRamp::advance() {
    while (pending_n_ > 0 && pending_[0].at <= clock_) {
        start(pending_[0].value);
        for (int i = 1; i < pending_n_; ++i) pending_[static_cast<std::size_t>(i - 1)] = pending_[static_cast<std::size_t>(i)];
        --pending_n_;
    }
    if (remaining_ > 0) {
        cur_db_ += step_db_; --remaining_;
        if (remaining_ == 0) cur_db_ = target_db_;
        gain_ = gain_of(cur_db_);
    }
    ++clock_;
    return gain_;
}

bool Switch::schedule(std::int64_t at, double v) {
    if (pending_n_ >= static_cast<int>(pending_.size())) return false;
    int i = pending_n_++;
    while (i > 0 && pending_[static_cast<std::size_t>(i - 1)].at > at) { pending_[static_cast<std::size_t>(i)] = pending_[static_cast<std::size_t>(i - 1)]; --i; }
    pending_[static_cast<std::size_t>(i)] = {at, v};
    return true;
}
double Switch::advance() {
    while (pending_n_ > 0 && pending_[0].at <= clock_) {
        value_ = pending_[0].value;
        for (int i = 1; i < pending_n_; ++i) pending_[static_cast<std::size_t>(i - 1)] = pending_[static_cast<std::size_t>(i)];
        --pending_n_;
    }
    ++clock_;
    return value_;
}

// ---------------------------------------------------------------- prepare
static bool sp_gain_step_valid(int db) { for (int s : A::SP_INPUT_GAIN_STEPS_DB) if (s == db) return true; return false; }

PrepareResult Engine::prepare(int host_rate, int channels, std::size_t max_block, const ProductParameters& product, const ResearchConfiguration* research) {
    prepared_ = false;
    auto fail = [](const char* code, const std::string& detail) { PrepareResult r; r.ok = false; r.code = code; r.detail = detail; return r; };
    bool rate_ok = false; for (int r : SUPPORTED_RATES) rate_ok |= (r == host_rate);
    if (!rate_ok) return fail("UNSUPPORTED_HOST_RATE", "host rate not in the supported set");
    if (channels < 1 || channels > 64) return fail("CHANNELS", "need 1..64 channels");
    if (max_block < 1 || max_block > MAX_BLOCK_LIMIT) return fail("MAX_BLOCK", "max_block must be 1..8192");
    research_ = research ? *research : ResearchConfiguration::checkpoint();
    const ResearchConfiguration& rc = research_;
    if (rc.slot_skew_enabled || rc.capture_offset_enabled) return fail("RESEARCH_SWITCH_NOT_PORTED", "slot skew / capture offset are research-only SP offsets not ported to the native core");
    if (rc.proxy_oversampling < 1 || rc.proxy_oversampling > 64) return fail("PROXY", "proxy_oversampling must be 1..64");
    if (rc.lobes < 1 || rc.sp_hw_s_host < 1 || rc.sp_hw_z_host < 1 || rc.r12_half_host < 1 || rc.mpc_hw_s_host < 1 || rc.hw_r < 1) return fail("KERNEL", "kernel sizes must be >= 1");
    if (std::string_view(A::SP_R3_STRATEGY) != "INACTIVE" || std::string_view(A::SP_R2_ANALOG_CLAMP) != "INACTIVE" || std::string_view(A::SP_R9_COUPLING_POLE) != "INACTIVE")
        return fail("R3_NOT_POPULATED", "only INACTIVE R3/clamp/coupling exist in the Track A asset");
    if (A::SP_HOLD_FRACTION != 1.0) return fail("HOLD_FRACTION", "only the full-period hold is implemented");
    if (std::string_view(A::MPC_R12_STRATEGY) != "TRANSPARENT" || std::string_view(A::MPC_R15_STRATEGY) != "TRANSPARENT" || std::string_view(A::MPC_R14_ARITHMETIC) != "IDENTITY_UNITY")
        return fail("MPC_STRATEGY_NOT_POPULATED", "only TRANSPARENT/IDENTITY_UNITY strategies exist");
    if (std::string_view(A::MPC_DE_EMPHASIS) != "OFF_UNASSERTED" || std::string_view(A::MPC_ADC_CODE_REPRESENTATION) != "ROUND_NEAREST_18BIT" || std::string_view(A::MPC_RECORD_LEVEL_LAW) != "IDEAL_DB_TRIM")
        return fail("MPC_ASSET", "unexpected MPC asset state");
    // product parameters
    if (product.physical_calibration) return fail("CALIBRATION_UNAVAILABLE", std::string("physical calibration requires Track B evidence (volts ") + A::SP_VOLTS_PER_NORMALIZED_UNIT + ")");
    { bool known = false, pop = false;
      for (const char* r : A::SP_ROUTES_KNOWN) known |= (product.sp_output_path == r);
      for (const char* r : A::SP_ROUTES_POPULATED) pop |= (product.sp_output_path == r);
      if (!known) return fail("ROUTE_UNKNOWN", "SP route not in asset");
      if (!pop) return fail("ROUTE_NOT_POPULATED", "SP route is NOT POPULATED (no guessed response)"); }
    { std::string_view st;
      if (product.mpc_output_route == "MAIN_LR") st = A::MPC_ROUTE_STATUS_MAIN_LR;
      else if (product.mpc_output_route == "INDIVIDUAL_PAIR") st = A::MPC_ROUTE_STATUS_INDIVIDUAL_PAIR;
      else if (product.mpc_output_route == "HEADPHONES") st = A::MPC_ROUTE_STATUS_HEADPHONES;
      else return fail("ROUTE_UNKNOWN", "MPC route not in asset");
      if (st == "EXCLUDED") return fail("ROUTE_EXCLUDED", "MPC route is EXCLUDED");
      if (st != "POPULATED") return fail("ROUTE_NOT_POPULATED", "MPC route is NOT POPULATED"); }
    if (product.sp_output_path != A::PRODUCT_SP_OUTPUT_PATH || product.mpc_output_route != A::PRODUCT_MPC_OUTPUT_ROUTE) return fail("ROUTE_NOT_PRODUCT", "route differs from the owner-approved product configuration");
    if (!sp_gain_step_valid(product.sp_input_gain_db)) return fail("SP_INPUT_GAIN", "sp_input_gain not an asset step");
    if (!(product.sp_input_level_db >= A::CTRL_SP_INPUT_LEVEL_DB_MIN && product.sp_input_level_db <= A::CTRL_SP_INPUT_LEVEL_DB_MAX)) return fail("CONTROL_RANGE", "sp_input_level_db outside the frozen control range");
    if (!(product.interstage_level_db >= A::PRODUCT_INTERSTAGE_RESEARCH_MIN_DB && product.interstage_level_db <= A::PRODUCT_INTERSTAGE_RESEARCH_MAX_DB)) return fail("INTERSTAGE_RANGE", "interstage_level_db outside the approved range");
    if (!(product.output_trim_db >= A::CTRL_OUTPUT_TRIM_DB_MIN && product.output_trim_db <= A::CTRL_OUTPUT_TRIM_DB_MAX)) return fail("CONTROL_RANGE", "output_trim_db outside the frozen control range");
    if (!(product.mpc_record_level_db <= 0.0) || !std::isfinite(product.mpc_record_level_db)) return fail("RECORD_LEVEL", "ideal trim is <= 0 dB");
    if (static_cast<int>(product.mpc_input_gain) < 0 || static_cast<int>(product.mpc_input_gain) > 2) return fail("MPC_INPUT_GAIN", "unknown gain position");
    if (rc.reverse_order_research && product.chain_mode != ChainMode::CASCADE) return fail("REVERSE_MODE", "reverse_order_research applies to CASCADE only");
    product_ = product; channels_ = channels; max_block_ = max_block; L_ = rc.proxy_oversampling;
    const int proxy_rate = host_rate * L_;
    // kernels (IMPLEMENTATION)
    std::string err; double dc_lp = 0.0, dc_12 = 0.0;
    if (!kaiser_sinc_lowpass(2 * rc.lobes * L_ + 1, 0.5 / static_cast<double>(L_), rc.lp_beta, h_lp_, dc_lp, err)) return fail("KERNEL", err);
    const double mpc_rate = static_cast<double>(A::MPC_RATE_NUM) / static_cast<double>(A::MPC_RATE_DEN);
    if (!kaiser_sinc_lowpass(2 * rc.r12_half_host * L_ + 1, (mpc_rate / 2.0) / static_cast<double>(proxy_rate), rc.r12_beta, h_r12_, dc_12, err)) return fail("KERNEL", err);
    RationalClock spc; spc.configure(A::SP_RATE_NUM, A::SP_RATE_DEN, proxy_rate);
    RationalClock mpcc; mpcc.configure(A::MPC_RATE_NUM, A::MPC_RATE_DEN, proxy_rate);
    const int sp_hw_s = rc.sp_hw_s_host * L_, sp_hw_z = rc.sp_hw_z_host * L_, mpc_hw_s = rc.mpc_hw_s_host * L_;
    if (!sp_taps_.build(sp_hw_s, rc.sp_interp_beta, spc.per_den, err)) return fail("TAP_TABLE", err);
    step_.build(sp_hw_z, rc.sp_interp_beta);
    if (!mpc_staps_.build(mpc_hw_s, rc.mpc_interp_beta, mpcc.per_den, err)) return fail("TAP_TABLE", err);
    if (!mpc_rtaps_.build(rc.hw_r, rc.mpc_interp_beta, mpcc.per_num, err)) return fail("TAP_TABLE", err);
    const std::size_t max_chunk = max_block * static_cast<std::size_t>(L_);
    SPCoreConfig sc; sc.rate_num = A::SP_RATE_NUM; sc.rate_den = A::SP_RATE_DEN; sc.proxy_rate = proxy_rate;
    sc.full_scale_codes = static_cast<double>(1 << (A::SP_WORD_BITS - 1)); sc.code_min = A::SP_CODE_MIN; sc.code_max = A::SP_CODE_MAX;
    sc.offset_codes = rc.quantizer_offset_codes; sc.dac_fs = A::SP_DAC_FULL_SCALE_NORMALIZED; sc.out_gain = A::SP_R9_OUTPUT_GAIN_NORMALIZED;
    sc.rule = static_cast<int>(rc.quantizer_rule); sc.quant_bypass = rc.quantizer_bypass; sc.hw_s = sp_hw_s; sc.hw_z = sp_hw_z; sc.max_chunk = max_chunk;
    MPCCoreConfig mc; mc.rate_num = A::MPC_RATE_NUM; mc.rate_den = A::MPC_RATE_DEN; mc.proxy_rate = proxy_rate;
    mc.c18_fs = static_cast<double>(1 << (A::MPC_CONVERTER_BITS - 1)); mc.c18_min = A::MPC_C18_MIN; mc.c18_max = A::MPC_C18_MAX; mc.c16_min = A::MPC_C16_MIN; mc.c16_max = A::MPC_C16_MAX;
    mc.expand = static_cast<double>(1 << (A::MPC_CONVERTER_BITS - A::MPC_STORAGE_BITS)); mc.dac_fs = A::MPC_DAC_FULL_SCALE_NORMALIZED;
    mc.rule = static_cast<int>(rc.reduction_rule); mc.quant_bypass = rc.converter_quant_bypass; mc.hw_s = mpc_hw_s; mc.hw_r = rc.hw_r; mc.L = L_; mc.max_chunk = max_chunk; mc.exact_reference_order = rc.exact_reference_order;
    up_.assign(static_cast<std::size_t>(channels), PolyphaseUpsampler()); down_.assign(static_cast<std::size_t>(channels), Decimator());
    sp_.assign(static_cast<std::size_t>(channels), SPCore()); mpc_.assign(static_cast<std::size_t>(channels), MPCCore());
    dly_sp_.assign(static_cast<std::size_t>(channels), DelayLine()); dly_mpc_.assign(static_cast<std::size_t>(channels), DelayLine()); bypass_.assign(static_cast<std::size_t>(channels), DelayLine());
    for (int c = 0; c < channels; ++c) {
        up_[static_cast<std::size_t>(c)].prepare(L_, h_lp_, max_block); down_[static_cast<std::size_t>(c)].prepare(L_, h_lp_, max_chunk);
        if (!sp_[static_cast<std::size_t>(c)].prepare(sc, &sp_taps_, &step_)) return fail("INTERNAL", "SP core table mismatch");
        if (!mpc_[static_cast<std::size_t>(c)].prepare(mc, h_r12_, h_lp_, &mpc_staps_, &mpc_rtaps_)) return fail("INTERNAL", "MPC core table mismatch");
    }
    d_sp_ = sp_[0].core_delay(); d_mpc_ = mpc_[0].core_delay(); r1_ = static_cast<std::int64_t>(rc.lobes) * L_;
    const std::int64_t delay_proxy = r1_ + d_sp_ + d_mpc_ + r1_;
    if (delay_proxy % L_ != 0) return fail("INTERNAL", "proxy delay not a multiple of L");
    const std::int64_t latency = delay_proxy / L_;
    for (int c = 0; c < channels; ++c) {
        dly_sp_[static_cast<std::size_t>(c)].prepare(static_cast<std::size_t>(d_sp_), max_chunk); dly_mpc_[static_cast<std::size_t>(c)].prepare(static_cast<std::size_t>(d_mpc_), max_chunk);
        bypass_[static_cast<std::size_t>(c)].prepare(static_cast<std::size_t>(latency), max_block);
    }
    xbuf_.assign(max_block, 0.0); ybuf_.assign(max_block, 0.0); bbuf_.assign(max_block, 0.0); gtrim_.assign(max_block, 0.0); gbyp_.assign(max_block, 0.0);
    vbuf_.assign(max_chunk, 0.0); hbuf_.assign(max_chunk, 0.0); hbuf2_.assign(max_chunk, 0.0); g2_.assign(max_chunk, 0.0); g10_.assign(max_chunk, 0.0); g11_.assign(max_chunk, 0.0);
    const std::int64_t ramp_proxy = std::llround(A::CTRL_RAMP_MS / 1000.0 * proxy_rate), ramp_host = std::llround(A::CTRL_RAMP_MS / 1000.0 * host_rate);
    ramp_sp_level_.configure(product.sp_input_level_db, ramp_proxy); ramp_interstage_.configure(product.interstage_level_db, ramp_proxy); ramp_trim_.configure(product.output_trim_db, ramp_host);
    g_mpc_record_ = db_to_gain(product.mpc_record_level_db);
    meters_.channel.assign(static_cast<std::size_t>(channels), ChannelMeters());
    // info
    const double A_lp = rc.lp_beta / 0.1102 + 8.7, A_12 = rc.r12_beta / 0.1102 + 8.7, A_is = rc.sp_interp_beta / 0.1102 + 8.7, A_im = rc.mpc_interp_beta / 0.1102 + 8.7;
    info_ = PreparedInfo();
    info_.host_rate = host_rate; info_.proxy_rate = proxy_rate; info_.L = L_; info_.channels = channels; info_.max_block = max_block;
    info_.chain_mode = product.chain_mode; info_.reverse_order_research = rc.reverse_order_research;
    info_.latency_host = latency; info_.r1_proxy = r1_; info_.sp_core_proxy = d_sp_; info_.mpc_core_proxy = d_mpc_; info_.r16_proxy = r1_;
    info_.sp_per_num = spc.per_num; info_.sp_per_den = spc.per_den; info_.mpc_per_num = mpcc.per_num; info_.mpc_per_den = mpcc.per_den;
    info_.mpc_D15 = mpc_[0].D15(); info_.mpc_r12_half = static_cast<std::int64_t>(rc.r12_half_host) * L_;
    info_.lowpass_taps = h_lp_.size(); info_.r12_taps = h_r12_.size(); info_.lowpass_dc_residual = dc_lp; info_.r12_dc_residual = dc_12; info_.step_truncation_residual = step_.truncation_residual;
    info_.sp_line_bound_relative = 2.0 * std::pow(10.0, -A_lp / 20) + std::pow(10.0, -A_is / 20) + step_.truncation_residual;
    info_.mpc_line_bound_relative = 2.0 * std::pow(10.0, -A_lp / 20) + std::pow(10.0, -A_12 / 20) + 2.0 * std::pow(10.0, -A_im / 20);
    info_.ramp_proxy_samples = ramp_proxy; info_.ramp_host_samples = ramp_host; info_.event_offset_r2_proxy = r1_; info_.event_offset_r10_proxy = r1_ + d_sp_;
    info_.sp_asset_sha256 = A::SP_ASSET_SHA256; info_.mpc_asset_sha256 = A::MPC_ASSET_SHA256; info_.product_config_sha256 = A::PRODUCT_CONFIG_SHA256; info_.controls_sha256 = A::CONTROLS_SHA256;
    info_.version = NATIVE_IMPLEMENTATION_VERSION; info_.exact_reference_order = rc.exact_reference_order;
    prepared_ = true;
    reset();
    PrepareResult ok; ok.ok = true; ok.code = "OK"; return ok;
}

void Engine::snap_params() {
    ramp_sp_level_.reset(product_.sp_input_level_db); ramp_interstage_.reset(product_.interstage_level_db); ramp_trim_.reset(product_.output_trim_db);
    sw_sp_step_.reset(static_cast<double>(product_.sp_input_gain_db)); sw_mpc_step_.reset(static_cast<double>(static_cast<int>(product_.mpc_input_gain))); sw_bypass_.reset(product_.plugin_bypass ? 1.0 : 0.0);
}

void Engine::update_product_targets(const ProductParameters& p) {
    product_.sp_input_level_db = p.sp_input_level_db; product_.sp_input_gain_db = p.sp_input_gain_db; product_.interstage_level_db = p.interstage_level_db;
    product_.mpc_input_gain = p.mpc_input_gain; product_.output_trim_db = p.output_trim_db; product_.plugin_bypass = p.plugin_bypass;
}

void Engine::reset() {
    if (!prepared_) return;
    for (int c = 0; c < channels_; ++c) {
        const auto i = static_cast<std::size_t>(c);
        up_[i].reset(); down_[i].reset(); sp_[i].reset(); mpc_[i].reset(); dly_sp_[i].reset(); dly_mpc_[i].reset(); bypass_[i].reset();
    }
    snap_params(); host_clock_ = 0; reset_meters(); meters_.fault_latched = false;
}

void Engine::reset_meters() {
    for (auto& m : meters_.channel) m = ChannelMeters();
    for (int c = 0; c < channels_; ++c) { sp_[static_cast<std::size_t>(c)].reset_meters(); mpc_[static_cast<std::size_t>(c)].reset_meters(); }
    meters_.nonfinite_input_samples = 0; meters_.faults = 0; meters_.events_rejected = 0;
}

void Engine::set_tap_sinks(int channel, TapSink* sp_codes, TapSink* mpc_c18, TapSink* mpc_c16) {
    const auto i = static_cast<std::size_t>(channel); sp_[i].tap_codes = sp_codes; mpc_[i].tap_c18 = mpc_c18; mpc_[i].tap_c16 = mpc_c16;
}

// ---------------------------------------------------------------- process
int Engine::process(const double* const* in, double* const* out, std::size_t frames, const ParamEvent* events, std::size_t n_events) {
    if (!prepared_) return -1;
    const std::int64_t faults0 = meters_.faults; std::size_t done = 0, ev_i = 0;
    do {
        const std::size_t n = std::min(max_block_, frames - done);
        // events for this chunk (offsets relative to the call); events must be sorted by offset
        const std::size_t ev_start = ev_i;
        while (ev_i < n_events && events[ev_i].offset < static_cast<std::int64_t>(done + n)) ++ev_i;
        process_chunk(in, out, n, events ? events + ev_start : nullptr, ev_i - ev_start, static_cast<std::int64_t>(done));
        done += n;
    } while (done < frames);
    const int faults = static_cast<int>(meters_.faults - faults0);
    // events with offsets beyond `frames` are rejected
    while (ev_i < n_events) { ++meters_.events_rejected; ++ev_i; }
    return static_cast<int>(faults);
}

void Engine::process_chunk(const double* const* in, double* const* out, std::size_t n, const ParamEvent* ev, std::size_t n_ev, std::int64_t host_rel0) {
    const std::size_t nL = n * static_cast<std::size_t>(L_);
    // 1. schedule parameter events (bounded queues; invalid events counted, never applied)
    for (std::size_t e = 0; e < n_ev; ++e) {
        const ParamEvent& p = ev[e];
        const std::int64_t rel = p.offset - host_rel0;
        if (rel < 0 || rel >= static_cast<std::int64_t>(n) || !std::isfinite(p.value)) { ++meters_.events_rejected; continue; }
        const std::int64_t abs_host = host_clock_ + rel, abs_proxy = abs_host * L_;
        bool ok = false;
        switch (p.id) {
            case ParamId::SP_INPUT_LEVEL_DB: if (p.value >= A::CTRL_SP_INPUT_LEVEL_DB_MIN && p.value <= A::CTRL_SP_INPUT_LEVEL_DB_MAX) { ok = ramp_sp_level_.schedule(abs_proxy + r1_, p.value); if (ok) product_.sp_input_level_db = p.value; } break;
            case ParamId::SP_INPUT_GAIN_DB: if (sp_gain_step_valid(static_cast<int>(p.value)) && p.value == std::floor(p.value)) { ok = sw_sp_step_.schedule(abs_proxy + r1_, p.value); if (ok) product_.sp_input_gain_db = static_cast<int>(p.value); } break;
            case ParamId::INTERSTAGE_LEVEL_DB: if (p.value >= A::PRODUCT_INTERSTAGE_RESEARCH_MIN_DB && p.value <= A::PRODUCT_INTERSTAGE_RESEARCH_MAX_DB) { ok = ramp_interstage_.schedule(abs_proxy + r1_ + d_sp_, p.value); if (ok) product_.interstage_level_db = p.value; } break;
            case ParamId::MPC_INPUT_GAIN: if (p.value == 0.0 || p.value == 1.0 || p.value == 2.0) { ok = sw_mpc_step_.schedule(abs_proxy + r1_ + d_sp_, p.value); if (ok) product_.mpc_input_gain = static_cast<MpcInputGain>(static_cast<int>(p.value)); } break;
            case ParamId::OUTPUT_TRIM_DB: if (p.value >= A::CTRL_OUTPUT_TRIM_DB_MIN && p.value <= A::CTRL_OUTPUT_TRIM_DB_MAX) { ok = ramp_trim_.schedule(abs_host, p.value); if (ok) product_.output_trim_db = p.value; } break;
            case ParamId::PLUGIN_BYPASS: if (p.value == 0.0 || p.value == 1.0) { ok = sw_bypass_.schedule(abs_host, p.value); if (ok) product_.plugin_bypass = p.value != 0.0; } break;
        }
        if (!ok) ++meters_.events_rejected;
    }
    // 2. gain trajectories, advanced once per sample of each clock domain (shared by all channels)
    double last_step = -1.0, g_step = 1.0, last_mstep = -1.0, g_mstep = 1.0;
    for (std::size_t i = 0; i < nL; ++i) {
        const double st = sw_sp_step_.advance();
        if (st != last_step) { g_step = db_to_gain(st); last_step = st; }
        g2_[i] = g_step * ramp_sp_level_.advance();                          // (10^(step/20)) * (10^(level/20)) as in the reference
        g10_[i] = ramp_interstage_.advance();
        const double ms = sw_mpc_step_.advance();
        if (ms != last_mstep) { g_mstep = db_to_gain(static_cast<double>(A::MPC_INPUT_GAIN_RELATIVE_DB[static_cast<int>(ms)])); last_mstep = ms; }
        g11_[i] = g_mstep * g_mpc_record_;
    }
    for (std::size_t m = 0; m < n; ++m) { gtrim_[m] = ramp_trim_.advance(); gbyp_[m] = sw_bypass_.advance(); }
    // 3. per channel
    bool fault = false;
    for (int c = 0; c < channels_; ++c) {
        const auto ci = static_cast<std::size_t>(c); ChannelMeters& cm = meters_.channel[ci];
        const double* x = in[ci] + host_rel0; double* y = out[ci] + host_rel0;
        double pk = cm.host_input_peak;
        for (std::size_t m = 0; m < n; ++m) {
            double v = x[m];
            if (!std::isfinite(v)) { v = 0.0; ++meters_.nonfinite_input_samples; }
            xbuf_[m] = v; const double a = std::fabs(v); if (a > pk) pk = a;
        }
        cm.host_input_peak = pk;
        up_[ci].process(xbuf_.data(), n, vbuf_.data());                           // R1
        bool host_done = false;
        switch (product_.chain_mode) {
            case ChainMode::CASCADE:
                if (!research_.reverse_order_research) {
                    sp_[ci].process(vbuf_.data(), g2_.data(), nL, hbuf_.data());                 // R2–R9
                    for (std::size_t i = 0; i < nL; ++i) hbuf_[i] = hbuf_[i] * g10_[i];          // R10
                    mpc_[ci].process_to_host(hbuf_.data(), g11_.data(), nL, ybuf_.data());      // R11–R15 then R16 (composed or exact order)
                    host_done = true;
                } else {                                                                          // INFORMATIONAL research only
                    mpc_[ci].process(vbuf_.data(), g11_.data(), nL, hbuf_.data());
                    for (std::size_t i = 0; i < nL; ++i) hbuf_[i] = hbuf_[i] * g10_[i];
                    sp_[ci].process(hbuf_.data(), g2_.data(), nL, hbuf2_.data());
                }
                break;
            case ChainMode::SP_ONLY: sp_[ci].process(vbuf_.data(), g2_.data(), nL, hbuf_.data()); dly_mpc_[ci].process(hbuf_.data(), nL, hbuf2_.data()); break;
            case ChainMode::MPC_ONLY: dly_sp_[ci].process(vbuf_.data(), nL, hbuf_.data()); mpc_[ci].process_to_host(hbuf_.data(), g11_.data(), nL, ybuf_.data()); host_done = true; break;
            default: dly_sp_[ci].process(vbuf_.data(), nL, hbuf_.data()); dly_mpc_[ci].process(hbuf_.data(), nL, hbuf2_.data()); break;
        }
        if (!host_done) down_[ci].process(hbuf2_.data(), nL, ybuf_.data());       // R16
        bypass_[ci].process(xbuf_.data(), n, bbuf_.data());                        // latency-aligned dry path (always running)
        double opk = cm.output_peak;
        for (std::size_t m = 0; m < n; ++m) {
            const double o = gbyp_[m] != 0.0 ? bbuf_[m] : ybuf_[m] * gtrim_[m];   // output trim is the final gain only
            y[m] = o; const double a = std::fabs(o); if (a > opk) opk = a;
            if (!std::isfinite(o)) fault = true;
        }
        cm.output_peak = opk;
        cm.sp_core_input_peak = sp_[ci].peak_core_input(); cm.mpc_core_input_peak = mpc_[ci].peak_core_input();
        cm.sp_clip = sp_[ci].clip_count(); cm.mpc_clip18 = mpc_[ci].clip18_count(); cm.mpc_clamp16 = mpc_[ci].clamp16_count();
    }
    if (fault) {   // documented fail-safe: silence this chunk, latch the fault, clear the signal state (parameters keep their targets)
        for (int c = 0; c < channels_; ++c) std::memset(out[static_cast<std::size_t>(c)] + host_rel0, 0, n * sizeof(double));
        ++meters_.faults; meters_.fault_latched = true;
        for (int c = 0; c < channels_; ++c) { const auto ci = static_cast<std::size_t>(c); up_[ci].reset(); down_[ci].reset(); sp_[ci].reset(); mpc_[ci].reset(); dly_sp_[ci].reset(); dly_mpc_[ci].reset(); bypass_[ci].reset(); }
        ramp_sp_level_.set_target_now(product_.sp_input_level_db); ramp_interstage_.set_target_now(product_.interstage_level_db); ramp_trim_.set_target_now(product_.output_trim_db);
    }
    host_clock_ += static_cast<std::int64_t>(n);
}

// ---------------------------------------------------------------- state v1
static std::string fmt17(double v) { char b[64]; std::snprintf(b, sizeof b, "%.17g", v); return b; }

std::string Engine::serialize_state_with_bypass(bool plugin_bypass) const {
    std::string s;
    s += "smlsp3000-state\n";
    s += "schema_version=" + std::to_string(A::CONTROLS_SCHEMA_VERSION) + "\n";
    s += std::string("controls=") + A::CONTROLS_ID + ";" + A::CONTROLS_SHA256 + "\n";
    s += std::string("product_config=") + A::PRODUCT_CONFIG_ID + ";" + A::PRODUCT_CONFIG_VERSION + ";" + A::PRODUCT_CONFIG_SHA256 + "\n";
    s += std::string("sp_asset=") + A::SP_ASSET_ID + ";" + A::SP_ASSET_VERSION + ";" + A::SP_MODEL_VERSION + ";" + A::SP_ASSET_SHA256 + "\n";
    s += std::string("mpc_asset=") + A::MPC_ASSET_ID + ";" + A::MPC_ASSET_VERSION + ";" + A::MPC_MODEL_VERSION + ";" + A::MPC_ASSET_SHA256 + "\n";
    s += "sp_input_level_db=" + fmt17(product_.sp_input_level_db) + "\n";
    s += "sp_input_gain_db=" + std::to_string(product_.sp_input_gain_db) + "\n";
    s += "interstage_level_db=" + fmt17(product_.interstage_level_db) + "\n";
    s += std::string("mpc_input_gain=") + mpc_gain_name(product_.mpc_input_gain) + "\n";
    s += "output_trim_db=" + fmt17(product_.output_trim_db) + "\n";
    s += std::string("plugin_bypass=") + (plugin_bypass ? "1" : "0") + "\n";
    return s;
}

StateLoadResult Engine::parse_state(std::string_view text, ProductParameters& out) {
    auto fail = [](const char* code, const std::string& d) { StateLoadResult r; r.ok = false; r.code = code; r.detail = d; return r; };
    std::size_t pos = 0; int line_no = 0; bool header = false;
    bool have[6] = {false, false, false, false, false, false}; bool ids_ok[5] = {false, false, false, false, false};
    ProductParameters p = out;
    auto parse_double = [](std::string_view v, double& d) { std::string t(v); char* end = nullptr; d = std::strtod(t.c_str(), &end); return end && *end == '\0' && !t.empty() && std::isfinite(d); };
    while (pos < text.size()) {
        std::size_t nl = text.find('\n', pos); if (nl == std::string_view::npos) nl = text.size();
        std::string_view line = text.substr(pos, nl - pos); pos = nl + 1; ++line_no;
        if (!line.empty() && line.back() == '\r') line.remove_suffix(1);
        if (line.empty()) continue;
        if (line_no == 1) { if (line != "smlsp3000-state") return fail("NOT_A_STATE_RECORD", "missing header line"); header = true; continue; }
        const std::size_t eq = line.find('='); if (eq == std::string_view::npos) return fail("MALFORMED_LINE", std::string(line));
        std::string_view key = line.substr(0, eq), val = line.substr(eq + 1); double d = 0.0;
        if (key == "schema_version") { if (val != std::to_string(A::CONTROLS_SCHEMA_VERSION)) return fail("UNSUPPORTED_SCHEMA_VERSION", "schema_version " + std::string(val) + " is not supported (only 1); no migration exists"); ids_ok[0] = true; }
        else if (key == "controls") { if (val != std::string(A::CONTROLS_ID) + ";" + A::CONTROLS_SHA256) return fail("ASSET_IDENTITY_MISMATCH", "controls identity differs"); ids_ok[1] = true; }
        else if (key == "product_config") { if (val != std::string(A::PRODUCT_CONFIG_ID) + ";" + A::PRODUCT_CONFIG_VERSION + ";" + A::PRODUCT_CONFIG_SHA256) return fail("ASSET_IDENTITY_MISMATCH", "product configuration identity differs"); ids_ok[2] = true; }
        else if (key == "sp_asset") { if (val != std::string(A::SP_ASSET_ID) + ";" + A::SP_ASSET_VERSION + ";" + A::SP_MODEL_VERSION + ";" + A::SP_ASSET_SHA256) return fail("ASSET_IDENTITY_MISMATCH", "SP asset identity differs"); ids_ok[3] = true; }
        else if (key == "mpc_asset") { if (val != std::string(A::MPC_ASSET_ID) + ";" + A::MPC_ASSET_VERSION + ";" + A::MPC_MODEL_VERSION + ";" + A::MPC_ASSET_SHA256) return fail("ASSET_IDENTITY_MISMATCH", "MPC asset identity differs"); ids_ok[4] = true; }
        else if (key == "sp_input_level_db") { if (!parse_double(val, d)) return fail("NON_FINITE_OR_MALFORMED", std::string(key)); if (d < A::CTRL_SP_INPUT_LEVEL_DB_MIN || d > A::CTRL_SP_INPUT_LEVEL_DB_MAX) return fail("OUT_OF_RANGE", std::string(key)); p.sp_input_level_db = d; have[0] = true; }
        else if (key == "sp_input_gain_db") { if (!parse_double(val, d) || d != std::floor(d) || !sp_gain_step_valid(static_cast<int>(d))) return fail("UNKNOWN_ENUM", std::string(key)); p.sp_input_gain_db = static_cast<int>(d); have[1] = true; }
        else if (key == "interstage_level_db") { if (!parse_double(val, d)) return fail("NON_FINITE_OR_MALFORMED", std::string(key)); if (d < A::PRODUCT_INTERSTAGE_RESEARCH_MIN_DB || d > A::PRODUCT_INTERSTAGE_RESEARCH_MAX_DB) return fail("OUT_OF_RANGE", std::string(key)); p.interstage_level_db = d; have[2] = true; }
        else if (key == "mpc_input_gain") { MpcInputGain g; if (!parse_mpc_gain(val, g)) return fail("UNKNOWN_ENUM", std::string(key)); p.mpc_input_gain = g; have[3] = true; }
        else if (key == "output_trim_db") { if (!parse_double(val, d)) return fail("NON_FINITE_OR_MALFORMED", std::string(key)); if (d < A::CTRL_OUTPUT_TRIM_DB_MIN || d > A::CTRL_OUTPUT_TRIM_DB_MAX) return fail("OUT_OF_RANGE", std::string(key)); p.output_trim_db = d; have[4] = true; }
        else if (key == "plugin_bypass") { if (val == "0") p.plugin_bypass = false; else if (val == "1") p.plugin_bypass = true; else return fail("UNKNOWN_ENUM", std::string(key)); have[5] = true; }
        else return fail("UNKNOWN_KEY", std::string(key) + " (research or calibration fields are never accepted)");
    }
    if (!header) return fail("NOT_A_STATE_RECORD", "empty");
    for (bool b : ids_ok) if (!b) return fail("MISSING_IDENTITY", "schema/controls/product/asset identity lines are required");
    for (bool b : have) if (!b) return fail("MISSING_FIELD", "every product control must be present");
    out = p; StateLoadResult r; r.ok = true; r.code = "OK"; return r;
}

}  // namespace smlsp3000
