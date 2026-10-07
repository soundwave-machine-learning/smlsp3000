// Native VST3 host harness (development/validation tool, Sprint 7): loads the built SML SP-3000 VST3 through JUCE's plugin
// hosting, renders raw float64 fixtures at a given rate/block/precision with optional parameter events (block-boundary
// delivery, as a host would), saves/restores state, reports latency, runs N instances, opens/closes the editor and times
// callbacks. Output is JSON on stdout. Not part of the product.
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>
#include <chrono>
#include <functional>
#include <cstdio>
#include <fstream>
#include <map>
#include <sstream>

static std::map<std::string, std::string> parse(int argc, char** argv) { std::map<std::string, std::string> m; for (int i = 1; i < argc; ++i) { std::string s = argv[i]; auto eq = s.find('='); if (eq != std::string::npos) m[s.substr(0, eq)] = s.substr(eq + 1); else m[s] = "1"; } return m; }
static std::string q(const std::string& s) { std::string o = "\""; for (char c : s) { if (c == '"' || c == '\\') { o += '\\'; o += c; } else if (c == '\n') o += "\\n"; else o += c; } return o + "\""; }
static bool read_f64(const std::string& p, std::vector<double>& v) { std::ifstream f(p, std::ios::binary); if (!f) return false; f.seekg(0, std::ios::end); auto n = f.tellg(); f.seekg(0); v.resize(static_cast<size_t>(n) / 8); f.read(reinterpret_cast<char*>(v.data()), static_cast<std::streamsize>(v.size() * 8)); return true; }
static bool write_bytes(const std::string& p, const void* d, size_t n) { std::ofstream f(p, std::ios::binary); if (!f) return false; f.write(static_cast<const char*>(d), static_cast<std::streamsize>(n)); return true; }

struct Ev { long long frame; std::string name; double value; };

// Hosted VST3 parameters are HostedAudioProcessorParameters (not AudioProcessorParameterWithID): match by display name and
// normalise by the frozen mapping (docs/PARAMETERS.md): dB linear in range, choice index/(n-1), bool 0/1.
struct PInfo { const char* id; const char* name; double lo, hi; int choices; };
static const PInfo kParams[6] = {{"sp_input_level_db", "SP Input Level", -60.0, 12.0, 0}, {"sp_input_gain", "SP Input Gain", 0, 0, 3}, {"interstage_level_db", "Interstage Level", -60.0, 24.0, 0}, {"mpc_input_gain", "MPC Input Gain", 0, 0, 3}, {"output_trim_db", "Output Trim", -60.0, 12.0, 0}, {"plugin_bypass", "Bypass", 0, 0, -1}};
static const PInfo* pinfo(const std::string& id) { for (auto& k : kParams) if (id == k.id) return &k; return nullptr; }
static juce::AudioProcessorParameter* find_param(juce::AudioPluginInstance& inst, const std::string& id) {
    const PInfo* k = pinfo(id); if (!k) return nullptr;
    for (auto* p : inst.getParameters()) if (p->getName(64).toStdString() == k->name) return p;
    return nullptr;
}
static float normalise(const std::string& id, double v) {
    const PInfo* k = pinfo(id); if (!k) return static_cast<float>(v);
    if (k->choices == -1) return v != 0.0 ? 1.0f : 0.0f;
    if (k->choices > 0) { double idx = v; if (id == "sp_input_gain") idx = (v >= 30.0 ? 2 : (v >= 10.0 ? 1 : 0)); return static_cast<float>(idx / (k->choices - 1)); }
    return static_cast<float>((v - k->lo) / (k->hi - k->lo));
}
static std::string id_of(juce::AudioProcessorParameter* p) { const std::string n = p->getName(64).toStdString(); for (auto& k : kParams) if (n == k.name) return k.id; return n; }

int main(int argc, char** argv) {
    juce::ScopedJuceInitialiser_GUI init;
    auto a = parse(argc, argv);
    const std::string plugin = a["plugin"]; const int rate = std::atoi(a.count("rate") ? a["rate"].c_str() : "48000"); const int block = std::atoi(a.count("block") ? a["block"].c_str() : "512");
    const bool dbl = a.count("precision") && a["precision"] == "64";
    juce::AudioPluginFormatManager fm; fm.addDefaultFormats();
    juce::OwnedArray<juce::PluginDescription> descs; juce::KnownPluginList list;
    for (auto* fmt : fm.getFormats()) list.scanAndAddFile(plugin, true, descs, *fmt);
    if (descs.isEmpty()) { std::printf("{\"ok\":false,\"error\":\"plugin not found or not loadable\"}\n"); return 2; }
    juce::String err;
    auto make = [&]() { auto inst = fm.createPluginInstance(*descs[0], rate, block, err); if (inst) { inst->enableAllBuses(); inst->setPlayConfigDetails(2, 2, rate, block); inst->setNonRealtime(a.count("offline") > 0); if (dbl && inst->supportsDoublePrecisionProcessing()) inst->setProcessingPrecision(juce::AudioProcessor::doublePrecision); inst->prepareToPlay(rate, block); } return inst; };
    std::unique_ptr<juce::AudioPluginInstance> inst = make();
    if (!inst) { std::printf("{\"ok\":false,\"error\":%s}\n", q(err.toStdString()).c_str()); return 3; }
    std::ostringstream o; o << "{\"ok\":true,\"name\":" << q(inst->getName().toStdString()) << ",\"latency\":" << inst->getLatencySamples() << ",\"double_supported\":" << (inst->supportsDoublePrecisionProcessing() ? "true" : "false") << ",\"precision\":" << (dbl ? 64 : 32)
      << ",\"format\":" << q(descs[0]->pluginFormatName.toStdString()) << ",\"uid\":" << q(descs[0]->createIdentifierString().toStdString()) << ",\"manufacturer\":" << q(descs[0]->manufacturerName.toStdString()) << ",\"version\":" << q(descs[0]->version.toStdString()) << ",\"category\":" << q(descs[0]->category.toStdString());
    // initial parameters (name=value)
    auto set_param = [&](juce::AudioPluginInstance& in, const std::string& name, double v) { if (auto* p = find_param(in, name)) p->setValueNotifyingHost(normalise(name, v)); else std::fprintf(stderr, "unknown parameter %s\n", name.c_str()); };
    for (auto& kv : a) if (kv.first.rfind("param.", 0) == 0) set_param(*inst, kv.first.substr(6), std::atof(kv.second.c_str()));
    // state restore before processing
    if (a.count("state_in")) { std::ifstream f(a["state_in"], std::ios::binary); std::vector<char> d((std::istreambuf_iterator<char>(f)), {}); inst->setStateInformation(d.data(), static_cast<int>(d.size())); o << ",\"state_in_bytes\":" << d.size();
        if (a.count("state_mutate")) {   // apply a deliberately invalid variant of the restored state on top; the plugin must leave the restored values untouched
            const std::string mut = a["state_mutate"]; juce::MemoryBlock mb(d.data(), d.size()); juce::MemoryBlock bad; std::string desc;
            // JUCE's VST3 host wraps the plugin's component state (base64) inside a "VST3PluginState" container: unwrap the IComponent stream,
            // parse the plugin's own SMLSP3000_STATE_V1 XML, mutate it, re-wrap and re-encode so the mutation really reaches the plugin
            std::unique_ptr<juce::XmlElement> host(juce::AudioProcessor::getXmlFromBinary(mb.getData(), static_cast<int>(mb.getSize())));
            std::unique_ptr<juce::XmlElement> xml; juce::MemoryBlock comp;
            if (host) if (auto* c = host->getChildByName("IComponent")) if (comp.fromBase64Encoding(c->getAllSubText())) xml = juce::AudioProcessor::getXmlFromBinary(comp.getData(), static_cast<int>(comp.getSize()));
            o << ",\"state_unwrapped_root\":" << q(xml ? xml->getTagName().toStdString() : std::string("none"));
            auto rewrite = [&](std::function<void(juce::XmlElement&)> f2) { if (!xml || !host) return; f2(*xml); juce::MemoryBlock inner; juce::AudioProcessor::copyXmlToBinary(*xml, inner);
                auto* c = host->getChildByName("IComponent"); c->deleteAllChildElements(); c->addTextElement(inner.toBase64Encoding()); juce::AudioProcessor::copyXmlToBinary(*host, bad); };
            if (mut == "garbage") { bad.setSize(4096); for (size_t i = 0; i < 4096; ++i) static_cast<char*>(bad.getData())[i] = static_cast<char>((i * 7919) & 0xff); desc = "4096 pseudo-random bytes"; }
            else if (mut == "truncate") { bad = juce::MemoryBlock(d.data(), d.size() / 2); desc = "first half of a valid blob"; }
            else if (mut == "oversize") { bad.setSize(3 * 1024 * 1024); bad.fillWith(0x41); desc = "3 MiB of 'A'"; }
            else if (mut == "future_schema") { rewrite([](juce::XmlElement& x) { x.setAttribute("schema_version", 2); }); desc = "wrapper schema_version=2"; }
            else if (mut == "identity") { rewrite([](juce::XmlElement& x) { auto* n = x.getChildByName("native"); juce::String t = n->getAllSubText().replace("sp_asset=sp1200", "sp_asset=sp1201"); n->deleteAllChildElements(); n->addTextElement(t); }); desc = "native sp_asset identity altered"; }
            else if (mut == "research_key") { rewrite([](juce::XmlElement& x) { auto* n = x.getChildByName("native"); juce::String t = n->getAllSubText() + "quantizer_rule=FLOOR\n"; n->deleteAllChildElements(); n->addTextElement(t); }); desc = "research key appended"; }
            else if (mut == "out_of_range") { rewrite([](juce::XmlElement& x) { auto* n = x.getChildByName("native"); juce::String t = n->getAllSubText().replace("output_trim_db=-1.5", "output_trim_db=40"); n->deleteAllChildElements(); n->addTextElement(t); }); desc = "output_trim_db=40 (out of range)"; }
            inst->setStateInformation(bad.getData(), static_cast<int>(bad.getSize())); o << ",\"state_mutation\":" << q(mut + ": " + desc + ", " + std::to_string(bad.getSize()) + " bytes"); } }
    // parameters/state given before playback are configured values: re-prepare = stream start (ENG-DEC-027), no ramp from stale values
    inst->releaseResources(); inst->prepareToPlay(rate, block);
    // events
    std::vector<Ev> events; if (a.count("events")) { std::ifstream f(a["events"]); std::string line; while (std::getline(f, line)) { if (line.empty() || line[0] == '#') continue; std::istringstream ls(line); Ev e; if (ls >> e.frame >> e.name >> e.value) events.push_back(e); } }
    // state load during processing at a frame: state_at=<frame> state_file=<file>
    const long long state_at = a.count("state_at") ? std::atoll(a["state_at"].c_str()) : -1;
    // render
    if (a.count("in")) {
        std::vector<double> inter; if (!read_f64(a["in"], inter)) { std::printf("{\"ok\":false,\"error\":\"cannot read input\"}\n"); return 2; }
        const size_t frames = inter.size() / 2; const size_t tail = a.count("drain") && a["drain"] == "0" ? 0 : static_cast<size_t>(inst->getLatencySamples()); const size_t total = frames + tail;
        std::vector<double> outd(total * 2, 0.0);
        std::vector<size_t> blocks; if (a.count("blocks")) { std::istringstream bs(a["blocks"]); std::string t; while (std::getline(bs, t, ',')) blocks.push_back(static_cast<size_t>(std::atoll(t.c_str()))); } else blocks.push_back(static_cast<size_t>(block));
        juce::AudioBuffer<float> bf(2, block * 2 + 8192); juce::AudioBuffer<double> bd(2, block * 2 + 8192); juce::MidiBuffer midi;
        size_t done = 0, bi = 0, ei = 0; std::vector<double> times;
        const bool bench = a.count("bench") > 0;
        while (done < total) {
            size_t n = blocks[bi % blocks.size()]; ++bi; if (n > total - done) n = total - done; if (n > static_cast<size_t>(bf.getNumSamples())) n = static_cast<size_t>(bf.getNumSamples());
            while (ei < events.size() && events[ei].frame <= static_cast<long long>(done)) { set_param(*inst, events[ei].name, events[ei].value); ++ei; }
            if (state_at >= 0 && static_cast<long long>(done) >= state_at && a.count("state_file")) { std::ifstream f(a["state_file"], std::ios::binary); std::vector<char> d((std::istreambuf_iterator<char>(f)), {}); inst->setStateInformation(d.data(), static_cast<int>(d.size())); a.erase("state_file"); o << ",\"state_applied_at_frame\":" << done; }
            if (dbl) { for (int c = 0; c < 2; ++c) for (size_t m = 0; m < n; ++m) bd.setSample(c, static_cast<int>(m), done + m < frames ? inter[(done + m) * 2 + static_cast<size_t>(c)] : 0.0);
                juce::AudioBuffer<double> view(bd.getArrayOfWritePointers(), 2, static_cast<int>(n)); const auto t0 = std::chrono::steady_clock::now(); if (a.count("host_bypass")) inst->processBlockBypassed(view, midi); else inst->processBlock(view, midi); if (bench) times.push_back(std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count());
                for (int c = 0; c < 2; ++c) for (size_t m = 0; m < n; ++m) outd[(done + m) * 2 + static_cast<size_t>(c)] = view.getSample(c, static_cast<int>(m)); }
            else { for (int c = 0; c < 2; ++c) for (size_t m = 0; m < n; ++m) bf.setSample(c, static_cast<int>(m), done + m < frames ? static_cast<float>(inter[(done + m) * 2 + static_cast<size_t>(c)]) : 0.0f);
                juce::AudioBuffer<float> view(bf.getArrayOfWritePointers(), 2, static_cast<int>(n)); const auto t0 = std::chrono::steady_clock::now(); if (a.count("host_bypass")) inst->processBlockBypassed(view, midi); else inst->processBlock(view, midi); if (bench) times.push_back(std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count());
                for (int c = 0; c < 2; ++c) for (size_t m = 0; m < n; ++m) outd[(done + m) * 2 + static_cast<size_t>(c)] = static_cast<double>(view.getSample(c, static_cast<int>(m))); }
            done += n;
        }
        if (a.count("out")) write_bytes(a["out"], outd.data(), outd.size() * 8);
        o << ",\"frames_in\":" << frames << ",\"frames_out\":" << total << ",\"blocks_used\":" << bi;
        if (bench && !times.empty()) { std::vector<double> s = times; std::sort(s.begin(), s.end()); double tot = 0; for (double t : times) tot += t; const double budget = static_cast<double>(block) / rate; auto pct = [&](double p) { return s[std::min(s.size() - 1, static_cast<size_t>(p * static_cast<double>(s.size() - 1) + 0.5))]; }; size_t over = 0; for (double t : times) if (t > budget) ++over;
            o << ",\"bench\":{\"calls\":" << times.size() << ",\"mean_load\":" << tot / (static_cast<double>(times.size()) * budget) << ",\"median_s\":" << pct(0.5) << ",\"p95_s\":" << pct(0.95) << ",\"p99_s\":" << pct(0.99) << ",\"p999_s\":" << pct(0.999) << ",\"max_s\":" << s.back() << ",\"budget_s\":" << budget << ",\"overruns\":" << over << "}";
            if (a.count("bench_raw")) write_bytes(a["bench_raw"], times.data(), times.size() * 8); }
    }
    // state save
    if (a.count("state_out")) { juce::MemoryBlock mb; inst->getStateInformation(mb); write_bytes(a["state_out"], mb.getData(), mb.getSize()); o << ",\"state_out_bytes\":" << mb.getSize(); }
    // parameters after everything
    o << ",\"params\":{"; bool first = true; for (auto* p : inst->getParameters()) { o << (first ? "" : ",") << q(id_of(p)) << ":{\"normalized\":" << p->getValue() << ",\"text\":" << q(p->getCurrentValueAsText().toStdString()) << ",\"name\":" << q(p->getName(64).toStdString()) << "}"; first = false; } o << "}";
    // multiple instances: render the same short input through N instances and report identical outputs
    if (a.count("instances")) { const int N = std::atoi(a["instances"].c_str()); std::vector<std::unique_ptr<juce::AudioPluginInstance>> insts; for (int i = 0; i < N; ++i) insts.push_back(make()); juce::AudioBuffer<float> b(2, block); juce::AudioBuffer<double> bdd(2, block); juce::MidiBuffer midi; std::vector<std::vector<double>> outs(static_cast<size_t>(N));
        for (int i = 0; i < N; ++i) { for (int k = 0; k < 50; ++k) { for (int c = 0; c < 2; ++c) for (int m = 0; m < block; ++m) { const double v = 0.5 * std::sin(0.01 * static_cast<double>(k * block + m)); b.setSample(c, m, static_cast<float>(v)); bdd.setSample(c, m, v); }
            if (dbl) { insts[static_cast<size_t>(i)]->processBlock(bdd, midi); for (int m = 0; m < block; ++m) outs[static_cast<size_t>(i)].push_back(bdd.getSample(0, m)); }   // instances inherit the precision they were prepared with
            else { insts[static_cast<size_t>(i)]->processBlock(b, midi); for (int m = 0; m < block; ++m) outs[static_cast<size_t>(i)].push_back(static_cast<double>(b.getSample(0, m))); } } }
        bool same = true; for (int i = 1; i < N; ++i) same &= (outs[static_cast<size_t>(i)] == outs[0]); o << ",\"instances\":" << N << ",\"instances_identical\":" << (same ? "true" : "false"); }
    // editor open/close
    if (a.count("editor")) { const int n = std::atoi(a["editor"].c_str()); int ok = 0; for (int i = 0; i < n; ++i) { std::unique_ptr<juce::AudioProcessorEditor> ed(inst->createEditorIfNeeded()); if (ed) { ed->setSize(920, 540); juce::MessageManager::getInstance()->runDispatchLoopUntil(30); ++ok; inst->editorBeingDeleted(ed.get()); } } o << ",\"editor_open_close\":" << ok; }
    // reprepare at a different block size / rate and reset
    if (a.count("reprepare")) { inst->releaseResources(); inst->setPlayConfigDetails(2, 2, rate, 64); inst->prepareToPlay(rate, 64); const int l1 = inst->getLatencySamples(); inst->reset(); inst->releaseResources(); inst->prepareToPlay(rate, block); o << ",\"reprepare_latency\":" << l1; }
    o << "}"; std::printf("%s\n", o.str().c_str());
    inst->releaseResources(); inst.reset();
    return 0;
}
