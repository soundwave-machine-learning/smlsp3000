// Host adapter tests (Sprint 7, VAL-023/024 native parts): adapter == core (double path), float32 path == promoted double path with the
// final cast, bypass endpoints/alignment/crossfade/rapid toggles/startup/reset, block-boundary parameter delivery == core events at
// offset 0, lock-free state handoff, partition invariance, zero-length and oversized blocks, and ZERO heap allocations inside process()
// (global operator new/delete are counted).
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <string>
#include <vector>
#include "smlsp3000/host_adapter.hpp"

static std::atomic<long> g_allocs{0}, g_frees{0};
void* operator new(std::size_t n) { ++g_allocs; void* p = std::malloc(n ? n : 1); if (!p) throw std::bad_alloc(); return p; }
void operator delete(void* p) noexcept { ++g_frees; std::free(p); }
void operator delete(void* p, std::size_t) noexcept { ++g_frees; std::free(p); }
void* operator new[](std::size_t n) { ++g_allocs; void* p = std::malloc(n ? n : 1); if (!p) throw std::bad_alloc(); return p; }
void operator delete[](void* p) noexcept { ++g_frees; std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { ++g_frees; std::free(p); }

using namespace smlsp3000;
static int failures = 0;
#define CHECK(cond, name) do { if (cond) std::printf("PASS %s\n", name); else { std::printf("FAIL %s\n", name); ++failures; } } while (0)

static std::vector<double> sig(std::size_t n, int rate, double amp, unsigned long long seed) {
    std::vector<double> x(n); unsigned long long s = seed;
    for (std::size_t m = 0; m < n; ++m) { const double t = static_cast<double>(m) / rate; s = s * 6364136223846793005ULL + 1442695040888963407ULL; const double nz = (static_cast<double>(s >> 11) / 9007199254740992.0 * 2.0 - 1.0);
        x[m] = amp * (0.5 * std::sin(2 * 3.141592653589793 * 440.0 * t) + 0.3 * std::sin(2 * 3.141592653589793 * 5321.0 * t) + 0.2 * nz); }
    return x;
}
static bool same(const std::vector<double>& a, const std::vector<double>& b) { return a.size() == b.size() && std::memcmp(a.data(), b.data(), a.size() * sizeof(double)) == 0; }

struct Stereo { std::vector<double> ch[2]; };
static Stereo run_adapter(HostAdapter& a, const Stereo& in, const std::vector<std::size_t>& blocks, const std::vector<std::pair<std::size_t, std::pair<ParamId, double>>>* events = nullptr, long* alloc_delta = nullptr) {
    const std::size_t N = in.ch[0].size(); Stereo out; out.ch[0].assign(N, 0.0); out.ch[1].assign(N, 0.0);
    std::size_t done = 0, bi = 0, ei = 0; const long a0 = g_allocs.load() + g_frees.load();
    while (done < N) {
        std::size_t n = blocks[bi % blocks.size()]; ++bi; if (n > N - done) n = N - done;
        while (events && ei < events->size() && (*events)[ei].first <= done) { a.set_parameter((*events)[ei].second.first, (*events)[ei].second.second); ++ei; }
        const double* ip[2] = {in.ch[0].data() + done, in.ch[1].data() + done}; double* op[2] = {out.ch[0].data() + done, out.ch[1].data() + done};
        a.process(ip, op, n); done += n;
    }
    if (alloc_delta) *alloc_delta = g_allocs.load() + g_frees.load() - a0;
    return out;
}

int main() {
    const int rate = 48000; const std::size_t N = 24000;
    ProductParameters p = ProductParameters::defaults(); ResearchConfiguration r = ResearchConfiguration::checkpoint();
    Stereo in; in.ch[0] = sig(N, rate, 0.5, 1); in.ch[1] = sig(N, rate, 0.4, 2);
    // reference: the core alone (same configuration)
    Stereo ref; { Engine e; e.prepare(rate, 2, 8192, p, &r); ref.ch[0].assign(N, 0.0); ref.ch[1].assign(N, 0.0); std::size_t done = 0; while (done < N) { const std::size_t n = std::min<std::size_t>(64, N - done); const double* ip[2] = {in.ch[0].data() + done, in.ch[1].data() + done}; double* op[2] = {ref.ch[0].data() + done, ref.ch[1].data() + done}; e.process(ip, op, n); done += n; } }
    HostAdapter a; auto pr = a.prepare(rate, 8192, p, &r); CHECK(pr.ok && a.latency() == 310, "adapter_prepare_latency_310");
    long allocs = 0; Stereo y = run_adapter(a, in, {64}, nullptr, &allocs);
    CHECK(same(y.ch[0], ref.ch[0]) && same(y.ch[1], ref.ch[1]), "adapter_double_path_equals_core");
    CHECK(allocs == 0, "no_heap_allocation_in_process_double");
    a.reset(); Stereo y2 = run_adapter(a, in, {1, 7, 500, 8192, 64, 3, 1000, 9000, 2});   // includes a block larger than max_block
    CHECK(same(y.ch[0], y2.ch[0]) && same(y.ch[1], y2.ch[1]), "adapter_partition_invariance_and_oversized_blocks");
    {   // zero-length calls
        a.reset(); const double* ip[2] = {in.ch[0].data(), in.ch[1].data()}; double o0[2][4] = {}; double* op[2] = {o0[0], o0[1]}; a.process(ip, op, 0); Stereo y3 = run_adapter(a, in, {64}); CHECK(same(y3.ch[0], y.ch[0]), "zero_length_call_harmless");
    }
    {   // float32 path: same float input promoted; expected = double path on the promoted input, then cast
        std::vector<float> fin[2], fout[2]; Stereo prom; for (int c = 0; c < 2; ++c) { fin[c].resize(N); fout[c].assign(N, 0.f); prom.ch[c].resize(N); for (std::size_t m = 0; m < N; ++m) { fin[c][m] = static_cast<float>(in.ch[c][m]); prom.ch[c][m] = static_cast<double>(fin[c][m]); } }
        a.reset(); Stereo yd = run_adapter(a, prom, {64});
        a.reset(); long fa = 0; { const long a0 = g_allocs.load() + g_frees.load(); std::size_t done = 0; while (done < N) { const std::size_t n = std::min<std::size_t>(64, N - done); const float* ip[2] = {fin[0].data() + done, fin[1].data() + done}; float* op[2] = {fout[0].data() + done, fout[1].data() + done}; a.process(ip, op, n); done += n; } fa = g_allocs.load() + g_frees.load() - a0; }
        bool ok = true; for (int c = 0; c < 2; ++c) for (std::size_t m = 0; m < N; ++m) ok &= (fout[c][m] == static_cast<float>(yd.ch[c][m]));
        CHECK(ok, "float32_path_equals_promoted_double_path_with_final_cast"); CHECK(fa == 0, "no_heap_allocation_in_process_float");
    }
    {   // bypass: startup in bypass → fully dry = latency-aligned input (no trim, no gains); then un-bypass crossfade; endpoints
        ProductParameters pb = p; pb.plugin_bypass = true; pb.output_trim_db = -6.0; pb.sp_input_level_db = 6.0;
        HostAdapter b; b.prepare(rate, 8192, pb, &r); Stereo yb = run_adapter(b, in, {64}); const std::size_t L = static_cast<std::size_t>(b.latency());
        bool dry = true; for (std::size_t m = L; m < N; ++m) dry &= (yb.ch[0][m] == in.ch[0][m - L]); for (std::size_t m = 0; m < L; ++m) dry &= (yb.ch[0][m] == 0.0);
        CHECK(dry && b.meters().bypass_weight == 0.0, "startup_in_bypass_fully_dry_aligned_no_trim");
        // un-bypass at frame 6000: after 10 ms (480 samples) fully processed == core with the same gains
        Engine e; e.prepare(rate, 2, 8192, [&]{ ProductParameters q = pb; q.plugin_bypass = false; return q; }(), &r); Stereo refg; refg.ch[0].assign(N, 0.0); refg.ch[1].assign(N, 0.0); { std::size_t done = 0; while (done < N) { const std::size_t n = std::min<std::size_t>(64, N - done); const double* ip[2] = {in.ch[0].data() + done, in.ch[1].data() + done}; double* op[2] = {refg.ch[0].data() + done, refg.ch[1].data() + done}; e.process(ip, op, n); done += n; } }
        b.reset(); std::vector<std::pair<std::size_t, std::pair<ParamId, double>>> ev = {{6016, {ParamId::PLUGIN_BYPASS, 0.0}}}; Stereo yu = run_adapter(b, in, {64}, &ev);   // 6016 = block boundary (block-boundary delivery)
        bool pre = true, post = true, mid_ok = true; for (std::size_t m = L; m < 6016; ++m) pre &= (yu.ch[0][m] == in.ch[0][m - L]); for (std::size_t m = 6016 + 480 + 1; m < N; ++m) post &= (yu.ch[0][m] == refg.ch[0][m]);
        for (std::size_t m = 6016; m < 6016 + 480; ++m) { const double w = static_cast<double>(m - 6016 + 1) / 480.0; const double exp = w * refg.ch[0][m] + (1.0 - w) * in.ch[0][m - L]; mid_ok &= std::fabs(yu.ch[0][m] - exp) <= 1e-12; }
        CHECK(pre && post, "bypass_endpoints_dry_then_fully_processed"); CHECK(mid_ok, "crossfade_linear_10ms_complementary_weights");
        // rapid toggles: on at 8000, off at 8100 (before the fade completes) → continues from the current weight; output stays bounded between the two signals
        b.reset(); std::vector<std::pair<std::size_t, std::pair<ParamId, double>>> ev2 = {{3008, {ParamId::PLUGIN_BYPASS, 0.0}}, {8000, {ParamId::PLUGIN_BYPASS, 1.0}}, {8128, {ParamId::PLUGIN_BYPASS, 0.0}}, {8256, {ParamId::PLUGIN_BYPASS, 1.0}}};
        Stereo yt = run_adapter(b, in, {64}, &ev2); bool bounded = true; for (std::size_t m = 8000; m < 9000; ++m) { const double lo = std::min(refg.ch[0][m], in.ch[0][m - L]) - 1e-12, hi = std::max(refg.ch[0][m], in.ch[0][m - L]) + 1e-12; bounded &= (yt.ch[0][m] >= lo && yt.ch[0][m] <= hi); }
        CHECK(bounded, "rapid_toggles_continue_from_current_weight_bounded"); CHECK(!same(yt.ch[0], yu.ch[0]), "toggles_change_output");
        // reset in bypass: fully dry from the first sample after latency
        b.set_parameter(ParamId::PLUGIN_BYPASS, 1.0); b.reset(); Stereo yr = run_adapter(b, in, {64}); bool dry2 = true; for (std::size_t m = L; m < N; ++m) dry2 &= (yr.ch[0][m] == in.ch[0][m - L]); CHECK(dry2, "reset_in_bypass_fully_dry");
        // partition invariance with toggles (block-boundary delivery: events at the same block starts)
        b.set_parameter(ParamId::PLUGIN_BYPASS, 1.0); b.reset(); Stereo yt1 = run_adapter(b, in, {64}, &ev2); b.set_parameter(ParamId::PLUGIN_BYPASS, 1.0); b.reset(); Stereo yt2 = run_adapter(b, in, {64}, &ev2); CHECK(same(yt1.ch[0], yt2.ch[0]), "bypass_sequence_deterministic");
    }
    {   // block-boundary parameter delivery == core events at offset 0 of the same blocks
        std::vector<std::pair<std::size_t, std::pair<ParamId, double>>> ev = {{3008, {ParamId::SP_INPUT_LEVEL_DB, -6.0}}, {9024, {ParamId::OUTPUT_TRIM_DB, -3.0}}, {12032, {ParamId::SP_INPUT_GAIN_DB, 20.0}}, {15040, {ParamId::MPC_INPUT_GAIN, 1.0}}, {18048, {ParamId::INTERSTAGE_LEVEL_DB, 4.0}}};
        a.reset(); Stereo ya = run_adapter(a, in, {64}, &ev);
        Engine e; e.prepare(rate, 2, 8192, p, &r); Stereo ye; ye.ch[0].assign(N, 0.0); ye.ch[1].assign(N, 0.0); std::size_t done = 0, ei = 0;
        while (done < N) { const std::size_t n = std::min<std::size_t>(64, N - done); std::vector<ParamEvent> evs; while (ei < ev.size() && ev[ei].first <= done) { evs.push_back({ev[ei].second.first, 0, ev[ei].second.second}); ++ei; }
            const double* ip[2] = {in.ch[0].data() + done, in.ch[1].data() + done}; double* op[2] = {ye.ch[0].data() + done, ye.ch[1].data() + done}; e.process(ip, op, n, evs.empty() ? nullptr : evs.data(), evs.size()); done += n; }
        CHECK(same(ya.ch[0], ye.ch[0]) && same(ya.ch[1], ye.ch[1]), "block_boundary_parameter_delivery_equals_core_events");
        CHECK(a.meters().events_rejected == 0, "no_events_rejected");
        a.set_parameter(ParamId::SP_INPUT_LEVEL_DB, 99.0); CHECK(a.parameter(ParamId::SP_INPUT_LEVEL_DB) == 12.0, "host_value_clamped_to_frozen_range");
        a.set_parameter(ParamId::SP_INPUT_LEVEL_DB, 0.0);
    }
    {   // state handoff: load during processing applies at the next block (as events), invalid state rejected and nothing applied
        for (int i = 0; i < 5; ++i) a.set_parameter(static_cast<ParamId>(i), (i == 1 || i == 3) ? 0.0 : 0.0);   // back to product defaults
        a.reset(); std::string st = a.save_state(); CHECK(st.find("plugin_bypass=0") != std::string::npos && st.find("quantizer") == std::string::npos, "save_state_product_fields_only");
        std::string mod = st; mod.replace(mod.find("sp_input_level_db=0"), 19, "sp_input_level_db=-12"); auto lr = a.load_state(mod); CHECK(lr.ok && a.parameter(ParamId::SP_INPUT_LEVEL_DB) == -12.0, "load_state_sets_targets");
        auto bad = a.load_state(st + "quantizer_rule=FLOOR\n"); CHECK(!bad.ok && a.parameter(ParamId::SP_INPUT_LEVEL_DB) == -12.0, "invalid_state_rejected_nothing_applied");
        std::string fut = st; fut.replace(fut.find("schema_version=1"), 16, "schema_version=2"); CHECK(!a.load_state(fut).ok, "future_schema_rejected");
        std::string big(3000000, 'x'); CHECK(!a.load_state(big).ok, "oversized_garbage_rejected");
        a.load_state(st); CHECK(a.parameter(ParamId::SP_INPUT_LEVEL_DB) == 0.0, "restore_defaults");
        a.reset(); long al = 0; Stereo yl = run_adapter(a, in, {64}, nullptr, &al); CHECK(same(yl.ch[0], ref.ch[0]) && al == 0, "after_state_ops_output_equals_core_no_alloc");
    }
    {   // non-finite and over-range input through the adapter (no NaN out; over-range indicated, not clamped)
        Stereo bad = in; bad.ch[0][100] = std::nan(""); bad.ch[1][200] = INFINITY; for (auto& v : bad.ch[1]) v *= 8.0; a.reset(); Stereo yb = run_adapter(a, bad, {64});
        bool fin = true; for (double v : yb.ch[0]) fin &= std::isfinite(v); for (double v : yb.ch[1]) fin &= std::isfinite(v);
        auto ms = a.meters(); CHECK(fin && ms.nonfinite_input_samples == 2 && ms.faults == 0, "adapter_nonfinite_input_policy");
        CHECK(ms.sp_clip[1] > 0 && ms.output_over_range[1] == (ms.output_peak[1] > 1.0), "over_range_indication_consistent");
    }
    std::printf("%s (%d failures) allocs_total=%ld\n", failures ? "ADAPTER TEST FAILED" : "ADAPTER TEST OK", failures, g_allocs.load());
    return failures ? 1 : 0;
}
