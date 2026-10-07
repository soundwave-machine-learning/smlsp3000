// Native offline render / info / kernel dump / benchmark / state tool for the SML SP-3000 core.
// The core itself does no I/O; this tool reads/writes raw float64 files (interleaved channels) for the Python harness.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include "smlsp3000/engine.hpp"

using namespace smlsp3000;

struct Args { std::vector<std::string> pos; std::vector<std::pair<std::string, std::string>> kv;
    std::string get(const std::string& k, const std::string& d = "") const { for (auto& p : kv) if (p.first == k) return p.second; return d; }
    bool has(const std::string& k) const { for (auto& p : kv) if (p.first == k) return true; return false; } };

static Args parse(int argc, char** argv) { Args a; for (int i = 1; i < argc; ++i) { std::string s = argv[i]; if (s.rfind("--", 0) == 0) { std::string k = s.substr(2); std::string v = "1"; if (i + 1 < argc && std::string(argv[i + 1]).rfind("--", 0) != 0) v = argv[++i]; a.kv.emplace_back(k, v); } else a.pos.push_back(s); } return a; }
static std::string q(const std::string& s) { std::string o = "\""; for (char c : s) { if (c == '"' || c == '\\') { o += '\\'; o += c; } else if (c == '\n') o += "\\n"; else if (c == '\r') o += "\\r"; else if (c == '\t') o += "\\t"; else o += c; } return o + "\""; }
static std::string f17(double v) { char b[64]; std::snprintf(b, sizeof b, "%.17g", v); return b; }

static bool build_config(const Args& a, ProductParameters& p, ResearchConfiguration& r, std::string& err) {
    p = ProductParameters::defaults(); r = ResearchConfiguration::checkpoint();
    if (a.has("sp-level")) p.sp_input_level_db = std::atof(a.get("sp-level").c_str());
    if (a.has("sp-gain")) p.sp_input_gain_db = std::atoi(a.get("sp-gain").c_str());
    if (a.has("interstage")) p.interstage_level_db = std::atof(a.get("interstage").c_str());
    if (a.has("mpc-gain") && !parse_mpc_gain(a.get("mpc-gain"), p.mpc_input_gain)) { err = "bad --mpc-gain"; return false; }
    if (a.has("trim")) p.output_trim_db = std::atof(a.get("trim").c_str());
    if (a.has("bypass")) p.plugin_bypass = a.get("bypass") != "0";
    if (a.has("mode") && !parse_chain_mode(a.get("mode"), p.chain_mode)) { err = "bad --mode"; return false; }
    if (a.has("record-level")) p.mpc_record_level_db = std::atof(a.get("record-level").c_str());
    if (a.has("sp-route")) p.sp_output_path = a.get("sp-route");
    if (a.has("mpc-route")) p.mpc_output_route = a.get("mpc-route");
    if (a.has("physical")) p.physical_calibration = a.get("physical") != "0";
    if (a.has("quantizer-rule")) r.quantizer_rule = a.get("quantizer-rule") == "FLOOR" ? QuantizerRule::FLOOR : QuantizerRule::ROUND_NEAREST;
    if (a.has("quantizer-offset")) r.quantizer_offset_codes = std::atof(a.get("quantizer-offset").c_str());
    if (a.has("quantizer-bypass")) r.quantizer_bypass = a.get("quantizer-bypass") != "0";
    if (a.has("reduction-rule")) r.reduction_rule = a.get("reduction-rule") == "TRUNCATION" ? ReductionRule::TRUNCATION : ReductionRule::ROUND_NEAREST;
    if (a.has("converter-bypass")) r.converter_quant_bypass = a.get("converter-bypass") != "0";
    if (a.has("proxy")) r.proxy_oversampling = std::atoi(a.get("proxy").c_str());
    if (a.has("lobes")) r.lobes = std::atoi(a.get("lobes").c_str());
    if (a.has("lp-beta")) r.lp_beta = std::atof(a.get("lp-beta").c_str());
    if (a.has("sp-hw-s")) r.sp_hw_s_host = std::atoi(a.get("sp-hw-s").c_str());
    if (a.has("sp-hw-z")) r.sp_hw_z_host = std::atoi(a.get("sp-hw-z").c_str());
    if (a.has("sp-interp-beta")) r.sp_interp_beta = std::atof(a.get("sp-interp-beta").c_str());
    if (a.has("r12-half")) r.r12_half_host = std::atoi(a.get("r12-half").c_str());
    if (a.has("r12-beta")) r.r12_beta = std::atof(a.get("r12-beta").c_str());
    if (a.has("mpc-hw-s")) r.mpc_hw_s_host = std::atoi(a.get("mpc-hw-s").c_str());
    if (a.has("hw-r")) r.hw_r = std::atoi(a.get("hw-r").c_str());
    if (a.has("mpc-interp-beta")) r.mpc_interp_beta = std::atof(a.get("mpc-interp-beta").c_str());
    if (a.has("reverse")) r.reverse_order_research = a.get("reverse") != "0";
    if (a.has("slot-skew")) r.slot_skew_enabled = a.get("slot-skew") != "0";
    if (a.has("exact-order")) r.exact_reference_order = a.get("exact-order") != "0";
    return true;
}

static std::string info_json(const PreparedInfo& i) {
    std::ostringstream o;
    o << "{\"version\":" << q(i.version) << ",\"host_rate\":" << i.host_rate << ",\"proxy_rate\":" << i.proxy_rate << ",\"L\":" << i.L << ",\"channels\":" << i.channels
      << ",\"max_block\":" << i.max_block << ",\"chain_mode\":" << q(chain_mode_name(i.chain_mode)) << ",\"reverse_order_research\":" << (i.reverse_order_research ? "true" : "false")
      << ",\"exact_reference_order\":" << (i.exact_reference_order ? "true" : "false") << ",\"latency_host_samples\":" << i.latency_host << ",\"latency_breakdown_proxy\":{\"R1\":" << i.r1_proxy << ",\"SP_core\":" << i.sp_core_proxy << ",\"MPC_core\":" << i.mpc_core_proxy << ",\"R16\":" << i.r16_proxy << "}"
      << ",\"sp_period_proxy\":\"" << i.sp_per_num << "/" << i.sp_per_den << "\",\"mpc_period_proxy\":\"" << i.mpc_per_num << "/" << i.mpc_per_den << "\",\"mpc_D15\":" << i.mpc_D15 << ",\"mpc_r12_half\":" << i.mpc_r12_half
      << ",\"lowpass_taps\":" << i.lowpass_taps << ",\"r12_taps\":" << i.r12_taps << ",\"lowpass_dc_residual\":" << f17(i.lowpass_dc_residual) << ",\"r12_dc_residual\":" << f17(i.r12_dc_residual)
      << ",\"step_truncation_residual\":" << f17(i.step_truncation_residual) << ",\"sp_line_bound_relative\":" << f17(i.sp_line_bound_relative) << ",\"mpc_line_bound_relative\":" << f17(i.mpc_line_bound_relative)
      << ",\"ramp_proxy_samples\":" << i.ramp_proxy_samples << ",\"ramp_host_samples\":" << i.ramp_host_samples << ",\"event_offset_r2_proxy\":" << i.event_offset_r2_proxy << ",\"event_offset_r10_proxy\":" << i.event_offset_r10_proxy
      << ",\"sp_asset_sha256\":" << q(i.sp_asset_sha256) << ",\"mpc_asset_sha256\":" << q(i.mpc_asset_sha256) << ",\"product_config_sha256\":" << q(i.product_config_sha256) << ",\"controls_sha256\":" << q(i.controls_sha256) << "}";
    return o.str();
}
static std::string meters_json(const Meters& m) {
    std::ostringstream o; o << "{\"channel\":[";
    for (std::size_t c = 0; c < m.channel.size(); ++c) { const auto& x = m.channel[c]; o << (c ? "," : "") << "{\"host_input_peak\":" << f17(x.host_input_peak) << ",\"sp_core_input_peak\":" << f17(x.sp_core_input_peak) << ",\"mpc_core_input_peak\":" << f17(x.mpc_core_input_peak)
        << ",\"output_peak\":" << f17(x.output_peak) << ",\"sp_clip\":" << x.sp_clip << ",\"mpc_clip18\":" << x.mpc_clip18 << ",\"mpc_clamp16\":" << x.mpc_clamp16 << "}"; }
    o << "],\"nonfinite_input_samples\":" << m.nonfinite_input_samples << ",\"faults\":" << m.faults << ",\"fault_latched\":" << (m.fault_latched ? "true" : "false") << ",\"events_rejected\":" << m.events_rejected << "}";
    return o.str();
}
static bool read_f64(const std::string& path, std::vector<double>& v) { std::ifstream f(path, std::ios::binary); if (!f) return false; f.seekg(0, std::ios::end); auto n = f.tellg(); f.seekg(0); v.resize(static_cast<std::size_t>(n) / 8); f.read(reinterpret_cast<char*>(v.data()), static_cast<std::streamsize>(v.size() * 8)); return true; }
static bool write_f64(const std::string& path, const double* d, std::size_t n) { std::ofstream f(path, std::ios::binary); if (!f) return false; f.write(reinterpret_cast<const char*>(d), static_cast<std::streamsize>(n * 8)); return true; }
static bool parse_param(const std::string& s, ParamId& id) {
    static const char* names[6] = {"sp_input_level_db", "sp_input_gain_db", "interstage_level_db", "mpc_input_gain", "output_trim_db", "plugin_bypass"};
    for (int i = 0; i < 6; ++i) if (s == names[i]) { id = static_cast<ParamId>(i); return true; } return false; }

static int cmd_info(const Args& a) {
    ProductParameters p; ResearchConfiguration r; std::string err; if (!build_config(a, p, r, err)) { std::cout << "{\"ok\":false,\"code\":\"ARGS\",\"detail\":" << q(err) << "}\n"; return 2; }
    Engine e; auto res = e.prepare(std::atoi(a.get("rate", "48000").c_str()), std::atoi(a.get("channels", "2").c_str()), static_cast<std::size_t>(std::atoi(a.get("max-block", "8192").c_str())), p, &r);
    if (!res.ok) { std::cout << "{\"ok\":false,\"code\":" << q(res.code) << ",\"detail\":" << q(res.detail) << "}\n"; return 3; }
    std::cout << "{\"ok\":true,\"info\":" << info_json(e.info()) << ",\"state\":" << q(e.serialize_state()) << "}\n"; return 0;
}

static int cmd_render(const Args& a) {
    ProductParameters p; ResearchConfiguration r; std::string err; if (!build_config(a, p, r, err)) { std::cout << "{\"ok\":false,\"code\":\"ARGS\",\"detail\":" << q(err) << "}\n"; return 2; }
    const int rate = std::atoi(a.get("rate", "48000").c_str()), ch = std::atoi(a.get("channels", "2").c_str()); const std::size_t max_block = static_cast<std::size_t>(std::atoi(a.get("max-block", "8192").c_str()));
    std::vector<double> inter; if (!read_f64(a.get("in"), inter)) { std::cout << "{\"ok\":false,\"code\":\"IO\",\"detail\":\"cannot read input\"}\n"; return 2; }
    const std::size_t frames = inter.size() / static_cast<std::size_t>(ch);
    Engine e; auto res = e.prepare(rate, ch, max_block, p, &r);
    if (!res.ok) { std::cout << "{\"ok\":false,\"code\":" << q(res.code) << ",\"detail\":" << q(res.detail) << "}\n"; return 3; }
    const std::size_t tail = a.get("drain", "1") != "0" ? static_cast<std::size_t>(e.latency()) : 0;
    const std::size_t total = frames + tail;
    std::vector<std::vector<double>> in(static_cast<std::size_t>(ch), std::vector<double>(total, 0.0)), out(static_cast<std::size_t>(ch), std::vector<double>(total, 0.0));
    for (std::size_t m = 0; m < frames; ++m) for (int c = 0; c < ch; ++c) in[static_cast<std::size_t>(c)][m] = inter[m * static_cast<std::size_t>(ch) + static_cast<std::size_t>(c)];
    // taps (offline diagnostics)
    std::vector<TapSink> sinks; std::vector<std::vector<double>> tapbuf; const bool taps = a.has("taps");
    if (taps) { sinks.resize(static_cast<std::size_t>(ch) * 3); tapbuf.resize(static_cast<std::size_t>(ch) * 3, std::vector<double>(total * 2 + 4096));
        for (int c = 0; c < ch; ++c) { for (int k = 0; k < 3; ++k) { auto& s = sinks[static_cast<std::size_t>(c * 3 + k)]; s.data = tapbuf[static_cast<std::size_t>(c * 3 + k)].data(); s.cap = tapbuf[static_cast<std::size_t>(c * 3 + k)].size(); }
            e.set_tap_sinks(c, &sinks[static_cast<std::size_t>(c * 3)], &sinks[static_cast<std::size_t>(c * 3 + 1)], &sinks[static_cast<std::size_t>(c * 3 + 2)]); } }
    // events file: lines "offset name value" (absolute frame offsets)
    std::vector<ParamEvent> events;
    if (a.has("events")) { std::ifstream f(a.get("events")); std::string line; while (std::getline(f, line)) { if (line.empty() || line[0] == '#') continue; std::istringstream ls(line); long long off; std::string name; double val; if (!(ls >> off >> name >> val)) continue; ParamId id; if (!parse_param(name, id)) { std::cout << "{\"ok\":false,\"code\":\"EVENT\",\"detail\":" << q(name) << "}\n"; return 2; } events.push_back({id, off, val}); } }
    // block schedule
    std::vector<std::size_t> blocks;
    if (a.has("blocks")) { std::istringstream bs(a.get("blocks")); std::string t; while (std::getline(bs, t, ',')) blocks.push_back(static_cast<std::size_t>(std::atoll(t.c_str()))); }
    else if (a.has("block-seed")) { unsigned long long s = static_cast<unsigned long long>(std::atoll(a.get("block-seed").c_str())); const std::size_t bmax = static_cast<std::size_t>(std::atoi(a.get("block-max", "8192").c_str()));
        std::size_t acc = 0; while (acc < total) { s = s * 6364136223846793005ULL + 1442695040888963407ULL; std::size_t b = 1 + static_cast<std::size_t>((s >> 33) % bmax); blocks.push_back(b); acc += b; } }
    else blocks.push_back(static_cast<std::size_t>(std::atoll(a.get("block", "8192").c_str())));
    std::vector<const double*> ip(static_cast<std::size_t>(ch)); std::vector<double*> op(static_cast<std::size_t>(ch));
    std::size_t done = 0, bi = 0, ev_i = 0; int faults = 0; std::vector<ParamEvent> evbuf;
    while (done < total) {
        std::size_t n = blocks[bi % blocks.size()]; ++bi; if (n > total - done) n = total - done;
        for (int c = 0; c < ch; ++c) { ip[static_cast<std::size_t>(c)] = in[static_cast<std::size_t>(c)].data() + done; op[static_cast<std::size_t>(c)] = out[static_cast<std::size_t>(c)].data() + done; }
        evbuf.clear(); while (ev_i < events.size() && events[ev_i].offset < static_cast<long long>(done + n)) { ParamEvent pe = events[ev_i]; pe.offset -= static_cast<long long>(done); evbuf.push_back(pe); ++ev_i; }
        faults += e.process(ip.data(), op.data(), n, evbuf.empty() ? nullptr : evbuf.data(), evbuf.size());
        done += n;
    }
    std::vector<double> outer(total * static_cast<std::size_t>(ch));
    for (std::size_t m = 0; m < total; ++m) for (int c = 0; c < ch; ++c) outer[m * static_cast<std::size_t>(ch) + static_cast<std::size_t>(c)] = out[static_cast<std::size_t>(c)][m];
    if (!write_f64(a.get("out"), outer.data(), outer.size())) { std::cout << "{\"ok\":false,\"code\":\"IO\",\"detail\":\"cannot write output\"}\n"; return 2; }
    std::ostringstream tj; tj << "[";
    if (taps) { static const char* kinds[3] = {"sp_codes", "mpc_c18", "mpc_c16"}; for (int c = 0; c < ch; ++c) for (int k = 0; k < 3; ++k) { const auto& s = sinks[static_cast<std::size_t>(c * 3 + k)]; const std::string path = a.get("taps") + "_ch" + std::to_string(c) + "_" + kinds[k] + ".f64"; write_f64(path, s.data, s.count); tj << ((c || k) ? "," : "") << "{\"channel\":" << c << ",\"kind\":" << q(kinds[k]) << ",\"count\":" << s.count << ",\"dropped\":" << s.dropped << ",\"path\":" << q(path) << "}"; } }
    tj << "]";
    std::cout << "{\"ok\":true,\"frames_in\":" << frames << ",\"frames_out\":" << total << ",\"tail\":" << tail << ",\"blocks_used\":" << bi << ",\"faults\":" << faults << ",\"info\":" << info_json(e.info()) << ",\"meters\":" << meters_json(e.meters()) << ",\"taps\":" << tj.str() << ",\"state\":" << q(e.serialize_state()) << "}\n";
    return 0;
}

static int cmd_dump_kernels(const Args& a) {
    ProductParameters p; ResearchConfiguration r; std::string err; if (!build_config(a, p, r, err)) { std::cout << "{\"ok\":false}\n"; return 2; }
    Engine e; auto res = e.prepare(std::atoi(a.get("rate", "48000").c_str()), 1, 64, p, &r);
    if (!res.ok) { std::cout << "{\"ok\":false,\"code\":" << q(res.code) << "}\n"; return 3; }
    const std::string pre = a.get("out-prefix");
    write_f64(pre + "_h_lp.f64", e.lowpass_taps().data(), e.lowpass_taps().size()); write_f64(pre + "_h_r12.f64", e.r12_taps().data(), e.r12_taps().size());
    write_f64(pre + "_sp_taps.f64", e.sp_sampler_table().table.data(), e.sp_sampler_table().table.size()); write_f64(pre + "_mpc_staps.f64", e.mpc_sampler_table().table.data(), e.mpc_sampler_table().table.size());
    write_f64(pre + "_mpc_rtaps.f64", e.mpc_recon_table().table.data(), e.mpc_recon_table().table.size()); write_f64(pre + "_step.f64", e.sp_step_table().table.data(), e.sp_step_table().table.size());
    std::cout << "{\"ok\":true,\"sp_taps_den\":" << e.sp_sampler_table().den << ",\"sp_taps_width\":" << e.sp_sampler_table().width << ",\"mpc_staps_den\":" << e.mpc_sampler_table().den << ",\"mpc_staps_width\":" << e.mpc_sampler_table().width
              << ",\"mpc_rtaps_den\":" << e.mpc_recon_table().den << ",\"mpc_rtaps_width\":" << e.mpc_recon_table().width << ",\"step_len\":" << e.sp_step_table().table.size() << ",\"step_truncation_residual\":" << f17(e.sp_step_table().truncation_residual) << ",\"info\":" << info_json(e.info()) << "}\n";
    return 0;
}

static int cmd_bench(const Args& a) {
    ProductParameters p; ResearchConfiguration r; std::string err; if (!build_config(a, p, r, err)) { std::cout << "{\"ok\":false}\n"; return 2; }
    const int rate = std::atoi(a.get("rate", "48000").c_str()), ch = std::atoi(a.get("channels", "2").c_str()); const std::size_t block = static_cast<std::size_t>(std::atoi(a.get("block", "64").c_str()));
    const double seconds = std::atof(a.get("seconds", "5").c_str()), warm = std::atof(a.get("warmup", "1").c_str()); const int trials = std::atoi(a.get("trials", "3").c_str());
    Engine e; auto res = e.prepare(rate, ch, block, p, &r); if (!res.ok) { std::cout << "{\"ok\":false,\"code\":" << q(res.code) << "}\n"; return 3; }
    // deterministic benchmark signal: three tones at -12 dBFS peak sum plus LCG noise at -40 dBFS (recorded in the result)
    std::vector<std::vector<double>> in(static_cast<std::size_t>(ch), std::vector<double>(block)), out(static_cast<std::size_t>(ch), std::vector<double>(block));
    std::vector<const double*> ip(static_cast<std::size_t>(ch)); std::vector<double*> op(static_cast<std::size_t>(ch));
    for (int c = 0; c < ch; ++c) { ip[static_cast<std::size_t>(c)] = in[static_cast<std::size_t>(c)].data(); op[static_cast<std::size_t>(c)] = out[static_cast<std::size_t>(c)].data(); }
    unsigned long long s = 12345; std::size_t t = 0;
    auto fill = [&]() { for (std::size_t m = 0; m < block; ++m, ++t) { const double tt = static_cast<double>(t) / rate; s = s * 6364136223846793005ULL + 1442695040888963407ULL; const double nz = (static_cast<double>(s >> 11) / 9007199254740992.0 * 2.0 - 1.0) * 0.01;
        const double v = 0.0837 * (std::sin(2 * 3.141592653589793 * 97.0 * tt) + std::sin(2 * 3.141592653589793 * 1003.0 * tt) + std::sin(2 * 3.141592653589793 * 7919.0 * tt)) + nz; for (int c = 0; c < ch; ++c) in[static_cast<std::size_t>(c)][m] = c == 0 ? v : -v * 0.5; } };
    const std::size_t warm_calls = static_cast<std::size_t>(warm * rate / static_cast<double>(block)); for (std::size_t i = 0; i < warm_calls; ++i) { fill(); e.process(ip.data(), op.data(), block); }
    const std::size_t calls = static_cast<std::size_t>(seconds * rate / static_cast<double>(block)); const double budget = static_cast<double>(block) / rate;
    std::ostringstream o; o << "{\"ok\":true,\"rate\":" << rate << ",\"channels\":" << ch << ",\"block\":" << block << ",\"seconds_per_trial\":" << seconds << ",\"warmup_seconds\":" << warm << ",\"calls_per_trial\":" << calls << ",\"callback_budget_s\":" << f17(budget)
      << ",\"signal\":\"3 tones (97/1003/7919 Hz) at 0.0837 each + LCG noise 0.01, ch1 inverted x0.5\",\"mode\":" << q(chain_mode_name(p.chain_mode)) << ",\"trials\":[";
    std::vector<double> times(calls);
    for (int tr = 0; tr < trials; ++tr) {
        double total = 0.0; for (std::size_t i = 0; i < calls; ++i) { fill(); const auto t0 = std::chrono::steady_clock::now(); e.process(ip.data(), op.data(), block); const auto t1 = std::chrono::steady_clock::now(); const double dt = std::chrono::duration<double>(t1 - t0).count(); times[i] = dt; total += dt; }
        std::vector<double> sorted = times; std::sort(sorted.begin(), sorted.end());
        auto pct = [&](double pp) { std::size_t i = static_cast<std::size_t>(pp * static_cast<double>(sorted.size() - 1) + 0.5); return sorted[std::min(i, sorted.size() - 1)]; };
        std::size_t over = 0; for (double d : times) if (d > budget) ++over;
        o << (tr ? "," : "") << "{\"mean_load\":" << f17(total / (static_cast<double>(calls) * budget)) << ",\"median_s\":" << f17(pct(0.5)) << ",\"p95_s\":" << f17(pct(0.95)) << ",\"p99_s\":" << f17(pct(0.99)) << ",\"p999_s\":" << f17(pct(0.999)) << ",\"max_s\":" << f17(sorted.back()) << ",\"min_s\":" << f17(sorted.front()) << ",\"overruns\":" << over << ",\"p999_over_budget\":" << f17(pct(0.999) / budget) << "}";
        if (a.has("raw")) write_f64(a.get("raw") + "_trial" + std::to_string(tr) + ".f64", times.data(), times.size());
    }
    o << "],\"checksum\":" << f17(out[0][block - 1]) << "}"; std::cout << o.str() << "\n"; return 0;
}

static int cmd_state(const Args& a) {
    ProductParameters p = ProductParameters::defaults(); std::string text; std::ifstream f(a.get("state")); std::stringstream ss; ss << f.rdbuf(); text = ss.str();
    auto r = Engine::parse_state(text, p);
    std::cout << "{\"ok\":" << (r.ok ? "true" : "false") << ",\"code\":" << q(r.code) << ",\"detail\":" << q(r.detail) << ",\"sp_input_level_db\":" << f17(p.sp_input_level_db) << ",\"sp_input_gain_db\":" << p.sp_input_gain_db << ",\"interstage_level_db\":" << f17(p.interstage_level_db)
              << ",\"mpc_input_gain\":" << q(mpc_gain_name(p.mpc_input_gain)) << ",\"output_trim_db\":" << f17(p.output_trim_db) << ",\"plugin_bypass\":" << (p.plugin_bypass ? "true" : "false") << "}\n"; return r.ok ? 0 : 4;
}

int main(int argc, char** argv) {
    Args a = parse(argc, argv);
    if (a.pos.empty()) { std::cerr << "usage: smlsp3000_native info|render|dump-kernels|bench|state-load [--options]\n"; return 1; }
    const std::string& cmd = a.pos[0];
    if (cmd == "info") return cmd_info(a); if (cmd == "render") return cmd_render(a); if (cmd == "dump-kernels") return cmd_dump_kernels(a); if (cmd == "bench") return cmd_bench(a); if (cmd == "state-load") return cmd_state(a);
    std::cerr << "unknown command\n"; return 1;
}
