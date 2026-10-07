// Native runtime self-test (ctest): determinism, partition invariance, chunking, zero/one-sample calls, non-finite input,
// over-range input, fail-safe, state v1 round trips and rejections, prepare rejections, latency/bypass alignment,
// automation trajectories across partitions, output-trim gain law. Exit code 0 = all pass.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include "smlsp3000/engine.hpp"

using namespace smlsp3000;
static int failures = 0;
#define CHECK(cond, name) do { if (cond) std::printf("PASS %s\n", name); else { std::printf("FAIL %s\n", name); ++failures; } } while (0)

static std::vector<double> signal(std::size_t n, int rate, double amp, unsigned long long seed) {
    std::vector<double> x(n); unsigned long long s = seed;
    for (std::size_t m = 0; m < n; ++m) { const double t = static_cast<double>(m) / rate; s = s * 6364136223846793005ULL + 1442695040888963407ULL; const double nz = (static_cast<double>(s >> 11) / 9007199254740992.0 * 2.0 - 1.0);
        x[m] = amp * (0.5 * std::sin(2 * 3.141592653589793 * 440.0 * t) + 0.3 * std::sin(2 * 3.141592653589793 * 5321.0 * t) + 0.2 * nz); }
    return x;
}
struct Run { std::vector<std::vector<double>> out; Meters meters; std::int64_t latency = 0; };
static Run render(const ProductParameters& p, const ResearchConfiguration& r, int rate, const std::vector<std::vector<double>>& in, const std::vector<std::size_t>& blocks, std::size_t max_block = 8192,
                  const std::vector<ParamEvent>* events = nullptr) {
    Engine e; auto res = e.prepare(rate, static_cast<int>(in.size()), max_block, p, &r); if (!res.ok) { std::printf("prepare failed %s %s\n", res.code.c_str(), res.detail.c_str()); std::exit(9); }
    const std::size_t total = in[0].size(); Run run; run.out.assign(in.size(), std::vector<double>(total, 0.0)); run.latency = e.latency();
    std::vector<const double*> ip(in.size()); std::vector<double*> op(in.size()); std::size_t done = 0, bi = 0, ev = 0; std::vector<ParamEvent> evb;
    while (done < total) { std::size_t n = blocks[bi % blocks.size()]; ++bi; if (n > total - done) n = total - done;
        for (std::size_t c = 0; c < in.size(); ++c) { ip[c] = in[c].data() + done; op[c] = run.out[c].data() + done; }
        evb.clear(); if (events) while (ev < events->size() && (*events)[ev].offset < static_cast<std::int64_t>(done + n)) { ParamEvent pe = (*events)[ev]; pe.offset -= static_cast<std::int64_t>(done); evb.push_back(pe); ++ev; }
        e.process(ip.data(), op.data(), n, evb.empty() ? nullptr : evb.data(), evb.size()); done += n; }
    run.meters = e.meters(); return run;
}
static bool same(const std::vector<double>& a, const std::vector<double>& b) { return a.size() == b.size() && std::memcmp(a.data(), b.data(), a.size() * sizeof(double)) == 0; }

int main() {
    const int rate = 48000; const std::size_t N = 24000;
    ProductParameters p = ProductParameters::defaults(); ResearchConfiguration r = ResearchConfiguration::checkpoint();
    std::vector<std::vector<double>> in = {signal(N, rate, 0.5, 1), signal(N, rate, 0.4, 2)};
    Run a = render(p, r, rate, in, {64});
    Run b = render(p, r, rate, in, {64});
    CHECK(same(a.out[0], b.out[0]) && same(a.out[1], b.out[1]), "same_build_determinism_repeat");
    Run c = render(p, r, rate, in, {1, 7, 500, 8192, 64, 3, 1000, 8191, 2});
    CHECK(same(a.out[0], c.out[0]) && same(a.out[1], c.out[1]), "block_partition_invariance_irregular");
    Run d = render(p, r, rate, in, {N});   // frames > max_block → internal chunking
    CHECK(same(a.out[0], d.out[0]) && same(a.out[1], d.out[1]), "internal_chunking_larger_than_max_block");
    Run e1 = render(p, r, rate, in, {64}, 64);   // prepared max_block 64 → every call chunked at 64
    CHECK(same(a.out[0], e1.out[0]), "max_block_64_identical");
    {   // zero-length and one-sample calls interleaved
        Engine e; e.prepare(rate, 2, 256, p, &r); std::vector<std::vector<double>> out(2, std::vector<double>(N, 0.0)); std::vector<const double*> ip(2); std::vector<double*> op(2);
        std::size_t done = 0; bool ok = true; while (done < N) { for (int c = 0; c < 2; ++c) { ip[static_cast<std::size_t>(c)] = in[static_cast<std::size_t>(c)].data() + done; op[static_cast<std::size_t>(c)] = out[static_cast<std::size_t>(c)].data() + done; }
            ok &= e.process(ip.data(), op.data(), 0) == 0; const std::size_t n = (done % 3 == 0) ? 1 : 200; const std::size_t nn = std::min(n, N - done); e.process(ip.data(), op.data(), nn); done += nn; }
        CHECK(ok && same(out[0], a.out[0]) && same(out[1], a.out[1]), "zero_length_and_one_sample_calls");
    }
    {   // non-finite input: replaced by zero, counted, no reset; equals the render with zeros in place
        auto in2 = in; in2[0][1000] = std::nan(""); in2[0][1001] = INFINITY; in2[1][5000] = -INFINITY; auto in3 = in; in3[0][1000] = 0.0; in3[0][1001] = 0.0; in3[1][5000] = 0.0;
        Run f = render(p, r, rate, in2, {64}); Run g = render(p, r, rate, in3, {64});
        CHECK(f.meters.nonfinite_input_samples == 3 && f.meters.faults == 0 && same(f.out[0], g.out[0]) && same(f.out[1], g.out[1]), "nonfinite_input_zeroed_counted_no_reset");
        bool finite = true; for (double v : f.out[0]) finite &= std::isfinite(v); CHECK(finite, "output_finite_after_nonfinite_input");
    }
    {   // over-range input ±16: finite, clamps counted, no host-boundary clamp of the input itself (bypass path passes ±16)
        auto in4 = in; for (auto& v : in4[0]) v *= 32.0; Run h = render(p, r, rate, in4, {64});
        bool finite = true; double pk = 0; for (double v : h.out[0]) { finite &= std::isfinite(v); pk = std::max(pk, std::fabs(v)); }
        CHECK(finite && h.meters.channel[0].sp_clip > 0 && h.meters.channel[0].host_input_peak > 15.0, "over_range_input_finite_clamps_counted");
        ProductParameters pb = p; pb.plugin_bypass = true; Run hb = render(pb, r, rate, in4, {64});
        bool pass = true; for (std::size_t m = static_cast<std::size_t>(hb.latency); m < N; ++m) pass &= (hb.out[0][m] == in4[0][m - static_cast<std::size_t>(hb.latency)]);
        for (std::size_t m = 0; m < static_cast<std::size_t>(hb.latency); ++m) pass &= hb.out[0][m] == 0.0;
        CHECK(pass, "plugin_bypass_exact_latency_aligned_dry_no_clamp");
    }
    {   // latency equal across chain modes and verified against the declared value with an impulse in the resampling-only mode
        std::int64_t lat[4]; for (int m = 0; m < 4; ++m) { ProductParameters pm = p; pm.chain_mode = static_cast<ChainMode>(m); Engine e; e.prepare(rate, 1, 64, pm, &r); lat[m] = e.latency(); }
        CHECK(lat[0] == lat[1] && lat[1] == lat[2] && lat[2] == lat[3] && lat[0] == 310, "latency_equal_all_modes_310_at_48k");
        ProductParameters pm = p; pm.chain_mode = ChainMode::BOTH_MACHINE_BYPASSED; std::vector<std::vector<double>> imp(1, std::vector<double>(4000, 0.0)); imp[0][100] = 1.0;
        Run ri = render(pm, r, rate, imp, {64}); std::size_t arg = 0; for (std::size_t m = 0; m < 4000; ++m) if (std::fabs(ri.out[0][m]) > std::fabs(ri.out[0][arg])) arg = m;
        CHECK(arg == 100 + static_cast<std::size_t>(ri.latency), "impulse_peak_at_declared_latency_resampling_path");
        std::int64_t lat96; { Engine e; e.prepare(96000, 1, 64, p, &r); lat96 = e.latency(); } CHECK(lat96 == 449, "latency_449_at_96k");
    }
    {   // automation: identical trajectories across partitions; ramp continues from the current value; events in later chunks
        std::vector<ParamEvent> ev = {{ParamId::SP_INPUT_LEVEL_DB, 3000, -6.0}, {ParamId::INTERSTAGE_LEVEL_DB, 3100, 3.0}, {ParamId::SP_INPUT_LEVEL_DB, 3200, 2.0}, {ParamId::OUTPUT_TRIM_DB, 9000, -3.0}, {ParamId::SP_INPUT_GAIN_DB, 12000, 20.0}, {ParamId::MPC_INPUT_GAIN, 15000, 1.0}, {ParamId::PLUGIN_BYPASS, 20000, 1.0}, {ParamId::PLUGIN_BYPASS, 21000, 0.0}};
        Run u = render(p, r, rate, in, {64}, 8192, &ev); Run v = render(p, r, rate, in, {1, 7, 500, 8192, 64, 3, 1000}, 8192, &ev); Run w = render(p, r, rate, in, {N}, 8192, &ev);
        CHECK(same(u.out[0], v.out[0]) && same(u.out[0], w.out[0]) && !same(u.out[0], a.out[0]), "automation_identical_across_partitions");
        std::vector<ParamEvent> bad = {{ParamId::SP_INPUT_LEVEL_DB, 10, 99.0}, {ParamId::MPC_INPUT_GAIN, 20, 7.0}, {ParamId::SP_INPUT_GAIN_DB, 30, 30.0}};
        Run x = render(p, r, rate, in, {64}, 8192, &bad); CHECK(x.meters.events_rejected == 3 && same(x.out[0], a.out[0]), "invalid_events_rejected_not_applied");
    }
    {   // output trim gain law: static trim multiplies the pre-trim output exactly by 10^(dB/20)
        ProductParameters pt = p; pt.output_trim_db = -6.0; Run t = render(pt, r, rate, in, {64}); const double g = std::pow(10.0, -6.0 / 20.0);
        bool pass = true; for (std::size_t m = 0; m < N; ++m) pass &= (t.out[0][m] == a.out[0][m] * g); CHECK(pass, "output_trim_static_gain_law_exact");
    }
    {   // state v1
        Engine e; e.prepare(rate, 2, 64, p, &r); std::string s = e.serialize_state(); ProductParameters q = ProductParameters::defaults(); q.sp_input_level_db = 5.0;
        auto lr = Engine::parse_state(s, q); CHECK(lr.ok && q.sp_input_level_db == 0.0 && q.mpc_input_gain == MpcInputGain::LO, "state_round_trip_defaults");
        ProductParameters p2 = p; p2.sp_input_level_db = -12.345678901234567; p2.interstage_level_db = 6.5; p2.sp_input_gain_db = 40; p2.mpc_input_gain = MpcInputGain::HI; p2.output_trim_db = -1.25; p2.plugin_bypass = true;
        Engine e2; e2.prepare(rate, 1, 64, p2, &r); ProductParameters q2 = ProductParameters::defaults(); auto lr2 = Engine::parse_state(e2.serialize_state(), q2);
        CHECK(lr2.ok && q2.sp_input_level_db == p2.sp_input_level_db && q2.interstage_level_db == 6.5 && q2.sp_input_gain_db == 40 && q2.mpc_input_gain == MpcInputGain::HI && q2.output_trim_db == -1.25 && q2.plugin_bypass, "state_round_trip_values_exact");
        std::string bad1 = s; bad1.replace(bad1.find("schema_version=1"), 16, "schema_version=2"); ProductParameters q3 = q2; auto l3 = Engine::parse_state(bad1, q3); CHECK(!l3.ok && l3.code == "UNSUPPORTED_SCHEMA_VERSION" && q3.sp_input_level_db == q2.sp_input_level_db, "state_rejects_future_schema_version_unchanged");
        std::string bad2 = s + "quantizer_rule=FLOOR\n"; auto l4 = Engine::parse_state(bad2, q3); CHECK(!l4.ok && l4.code == "UNKNOWN_KEY", "state_rejects_research_key");
        std::string bad3 = s; bad3.replace(bad3.find("sp_input_level_db=0"), 19, "sp_input_level_db=99"); auto l5 = Engine::parse_state(bad3, q3); CHECK(!l5.ok && l5.code == "OUT_OF_RANGE", "state_rejects_out_of_range");
        std::string bad4 = s; bad4.replace(bad4.find("sp_asset="), 9, "sp_asset=x"); auto l6 = Engine::parse_state(bad4, q3); CHECK(!l6.ok && l6.code == "ASSET_IDENTITY_MISMATCH", "state_rejects_asset_identity_mismatch");
        auto l7 = Engine::parse_state("hello\n", q3); CHECK(!l7.ok && l7.code == "NOT_A_STATE_RECORD", "state_rejects_non_record");
        std::string bad5 = s; bad5.replace(bad5.find("mpc_input_gain=LO"), 17, "mpc_input_gain=XX"); auto l8 = Engine::parse_state(bad5, q3); CHECK(!l8.ok && l8.code == "UNKNOWN_ENUM", "state_rejects_unknown_enum");
    }
    {   // prepare rejections
        auto rej = [&](ProductParameters pp, ResearchConfiguration rr, const char* code) { Engine e; auto res = e.prepare(rate, 1, 64, pp, &rr); return !res.ok && res.code == code; };
        ProductParameters p1 = p; p1.physical_calibration = true; CHECK(rej(p1, r, "CALIBRATION_UNAVAILABLE"), "prepare_rejects_physical_calibration");
        ProductParameters p2 = p; p2.sp_output_path = "FIXED_CH5_6"; CHECK(rej(p2, r, "ROUTE_NOT_POPULATED"), "prepare_rejects_unpopulated_sp_route");
        ProductParameters p3 = p; p3.mpc_output_route = "HEADPHONES"; CHECK(rej(p3, r, "ROUTE_EXCLUDED"), "prepare_rejects_excluded_mpc_route");
        ProductParameters p4 = p; p4.sp_input_gain_db = 30; CHECK(rej(p4, r, "SP_INPUT_GAIN"), "prepare_rejects_bad_gain_step");
        ProductParameters p5 = p; p5.interstage_level_db = 25.0; CHECK(rej(p5, r, "INTERSTAGE_RANGE"), "prepare_rejects_interstage_range");
        ResearchConfiguration r1 = r; r1.slot_skew_enabled = true; CHECK(rej(p, r1, "RESEARCH_SWITCH_NOT_PORTED"), "prepare_rejects_unported_research_switch");
        Engine e; auto res = e.prepare(50000, 1, 64, p, &r); CHECK(!res.ok && res.code == "UNSUPPORTED_HOST_RATE", "prepare_rejects_unsupported_rate");
        auto res2 = e.prepare(rate, 1, 9000, p, &r); CHECK(!res2.ok && res2.code == "MAX_BLOCK", "prepare_rejects_max_block_over_8192");
    }
    {   // reset reproduces the stream from the beginning
        Engine e; e.prepare(rate, 2, 64, p, &r); std::vector<std::vector<double>> o1(2, std::vector<double>(N)), o2(2, std::vector<double>(N)); std::vector<const double*> ip(2); std::vector<double*> op(2);
        for (int pass = 0; pass < 2; ++pass) { auto& o = pass ? o2 : o1; std::size_t done = 0; while (done < N) { const std::size_t n = std::min<std::size_t>(64, N - done); for (int c = 0; c < 2; ++c) { ip[static_cast<std::size_t>(c)] = in[static_cast<std::size_t>(c)].data() + done; op[static_cast<std::size_t>(c)] = o[static_cast<std::size_t>(c)].data() + done; } e.process(ip.data(), op.data(), n); done += n; } e.reset(); }
        CHECK(same(o1[0], o2[0]) && same(o1[1], o2[1]) && same(o1[0], a.out[0]), "reset_reproduces_stream");
    }
    std::printf("%s (%d failures)\n", failures ? "SELFTEST FAILED" : "SELFTEST OK", failures);
    return failures ? 1 : 0;
}
