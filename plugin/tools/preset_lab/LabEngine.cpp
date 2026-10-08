#include "LabEngine.h"
#include <cmath>
#include <juce_cryptography/juce_cryptography.h>
#include "track_a_assets_v1.hpp"

namespace preset_lab {
using namespace smlsp3000;

juce::String ClampReport::text() const {
    juce::String s;
    s << "SP 12-bit clamps: L " << juce::String(sp_clip[0]) << "  R " << juce::String(sp_clip[1]) << "\n";
    s << "MPC 18-bit clamps: L " << juce::String(mpc_clip18[0]) << "  R " << juce::String(mpc_clip18[1]) << "\n";
    s << "16-bit storage clamps: L " << juce::String(mpc_clamp16[0]) << "  R " << juce::String(mpc_clamp16[1]) << "\n";
    s << "Output over-range: " << ((output_over_range[0] || output_over_range[1]) ? "YES" : "NO") << "\n";
    if (nonfinite_input > 0) s << "Non-finite input samples replaced by zero: " << juce::String(nonfinite_input) << "\n";
    if (faults > 0) s << "Internal faults: " << juce::String(faults) << "\n";
    return s;
}

FileAnalysis analyse(const juce::AudioBuffer<double>& b) {
    FileAnalysis a; a.frames = b.getNumSamples(); a.channels = b.getNumChannels();
    for (int c = 0; c < juce::jmin(2, b.getNumChannels()); ++c) {
        const double* x = b.getReadPointer(c); double pk = 0.0, ss = 0.0;
        for (int i = 0; i < b.getNumSamples(); ++i) { const double v = std::fabs(x[i]); if (v > pk) pk = v; ss += x[i] * x[i]; }
        a.peak[c] = pk; a.rms[c] = b.getNumSamples() > 0 ? std::sqrt(ss / b.getNumSamples()) : 0.0;
    }
    return a;
}

static const char* kNames[6] = {"sp_input_level_db", "sp_input_gain_db", "interstage_level_db", "mpc_input_gain", "output_trim_db", "plugin_bypass"};

juce::var RenderRecord::toVar(const juce::String& toolBuildId, const juce::String& sourcePath, const juce::String& outputPath) const {
    auto* r = new juce::DynamicObject();
    r->setProperty("record", "smlsp3000-preset-lab-render"); r->setProperty("schema", 1); r->setProperty("ok", ok); if (!ok) r->setProperty("error", error);
    r->setProperty("tool_version", TOOL_VERSION); r->setProperty("tool_build_id", toolBuildId);
    r->setProperty("native_core_version", NATIVE_IMPLEMENTATION_VERSION); r->setProperty("adapter_version", HOST_ADAPTER_VERSION); r->setProperty("product_version", "0.7.0");
    r->setProperty("candidate_id", candidate_id); r->setProperty("candidate_revision", candidate_revision);
    r->setProperty("source_path", sourcePath); r->setProperty("source_sha256", source_sha256); r->setProperty("output_path", outputPath);
    r->setProperty("output_file_sha256", output_file_sha256); r->setProperty("output_f64_sha256", output_f64_sha256);
    r->setProperty("rate", rate); r->setProperty("block", block); r->setProperty("frames_in", static_cast<juce::int64>(frames_in)); r->setProperty("frames_out", static_cast<juce::int64>(frames_out)); r->setProperty("latency", static_cast<juce::int64>(latency));
    auto* sp = new juce::DynamicObject();
    sp->setProperty("sp_input_level_db", stored.sp_input_level_db); sp->setProperty("sp_input_gain_db", stored.sp_input_gain_db); sp->setProperty("interstage_level_db", stored.interstage_level_db);
    sp->setProperty("mpc_input_gain", juce::String(mpc_gain_name(stored.mpc_input_gain))); sp->setProperty("output_trim_db", stored.output_trim_db); sp->setProperty("plugin_bypass", stored.plugin_bypass);
    r->setProperty("product_parameters", juce::var(sp));
    auto* ev = new juce::DynamicObject(); for (int i = 0; i < 6; ++i) ev->setProperty(kNames[i], effective.v[i]); r->setProperty("effective_host_mapped_values", juce::var(ev));
    r->setProperty("effective_note", "values the adapter holds after the plugin's float32 normalised parameter mapping (what a DAW or a session restore delivers); the render used these");
    auto* cl = new juce::DynamicObject();
    cl->setProperty("sp_clip", juce::Array<juce::var>{static_cast<juce::int64>(clamps.sp_clip[0]), static_cast<juce::int64>(clamps.sp_clip[1])});
    cl->setProperty("mpc_clip18", juce::Array<juce::var>{static_cast<juce::int64>(clamps.mpc_clip18[0]), static_cast<juce::int64>(clamps.mpc_clip18[1])});
    cl->setProperty("mpc_clamp16", juce::Array<juce::var>{static_cast<juce::int64>(clamps.mpc_clamp16[0]), static_cast<juce::int64>(clamps.mpc_clamp16[1])});
    cl->setProperty("output_over_range", juce::Array<juce::var>{clamps.output_over_range[0], clamps.output_over_range[1]});
    cl->setProperty("nonfinite_input", static_cast<juce::int64>(clamps.nonfinite_input)); cl->setProperty("faults", static_cast<juce::int64>(clamps.faults));
    r->setProperty("clamp_report", juce::var(cl));
    auto an = [](const FileAnalysis& a) { auto* o = new juce::DynamicObject(); o->setProperty("sample_peak", juce::Array<juce::var>{a.peak[0], a.peak[1]}); o->setProperty("rms", juce::Array<juce::var>{a.rms[0], a.rms[1]}); o->setProperty("frames", static_cast<juce::int64>(a.frames)); o->setProperty("note", "offline file analysis of the whole buffer (sample peak, RMS of samples); audition-only level information, not a plugin meter, not LUFS, not true peak"); return juce::var(o); };
    r->setProperty("source_analysis", an(source)); r->setProperty("output_analysis", an(output));
    return juce::var(r);
}

LabEngine::LabEngine() { formats_.registerBasicFormats(); }

const juce::StringArray& LabEngine::supportedRates() { static const juce::StringArray r{"44100", "48000", "88200", "96000", "176400", "192000"}; return r; }

void LabEngine::applyThroughHostParameters(SMLProcessor& proc, const ProductParameters& p) {
    auto setF = [&](ParamId id, double v) { auto* prm = static_cast<juce::AudioParameterFloat*>(proc.parameterFor(id)); prm->setValueNotifyingHost(prm->convertTo0to1(static_cast<float>(v))); };
    setF(ParamId::SP_INPUT_LEVEL_DB, p.sp_input_level_db); setF(ParamId::INTERSTAGE_LEVEL_DB, p.interstage_level_db); setF(ParamId::OUTPUT_TRIM_DB, p.output_trim_db);
    { auto* prm = static_cast<juce::AudioParameterChoice*>(proc.parameterFor(ParamId::SP_INPUT_GAIN_DB)); int idx = 0; for (int k = 0; k < 3; ++k) if (assets_v1::SP_INPUT_GAIN_STEPS_DB[k] == p.sp_input_gain_db) idx = k; prm->setValueNotifyingHost(prm->convertTo0to1(static_cast<float>(idx))); }
    { auto* prm = static_cast<juce::AudioParameterChoice*>(proc.parameterFor(ParamId::MPC_INPUT_GAIN)); prm->setValueNotifyingHost(prm->convertTo0to1(static_cast<float>(static_cast<int>(p.mpc_input_gain)))); }
    { auto* prm = static_cast<juce::AudioParameterBool*>(proc.parameterFor(ParamId::PLUGIN_BYPASS)); prm->setValueNotifyingHost(p.plugin_bypass ? 1.0f : 0.0f); }
}

EffectiveValues LabEngine::effectiveValues(const SMLProcessor& proc) { EffectiveValues e; for (int i = 0; i < 6; ++i) e.v[i] = const_cast<SMLProcessor&>(proc).adapter().parameter(static_cast<ParamId>(i)); return e; }

ProductParameters LabEngine::readBackFromAdapter(const SMLProcessor& proc) {
    auto e = effectiveValues(proc); ProductParameters p = ProductParameters::defaults();
    p.sp_input_level_db = e.v[0]; p.sp_input_gain_db = static_cast<int>(e.v[1]); p.interstage_level_db = e.v[2]; p.mpc_input_gain = static_cast<MpcInputGain>(static_cast<int>(e.v[3])); p.output_trim_db = e.v[4]; p.plugin_bypass = e.v[5] != 0.0;
    return p;
}

ClampReport LabEngine::clampReportFrom(const MeterSnapshot& m) {
    ClampReport r; for (int c = 0; c < 2; ++c) { r.sp_clip[c] = m.sp_clip[c]; r.mpc_clip18[c] = m.mpc_clip18[c]; r.mpc_clamp16[c] = m.mpc_clamp16[c]; r.output_over_range[c] = m.output_over_range[c]; }
    r.nonfinite_input = m.nonfinite_input_samples; r.faults = m.faults; return r;
}

juce::String LabEngine::sha256(const void* data, std::size_t bytes) { return juce::SHA256(data, bytes).toHexString(); }
juce::String LabEngine::sha256(const juce::AudioBuffer<double>& b) {
    std::vector<double> inter(static_cast<std::size_t>(b.getNumSamples()) * static_cast<std::size_t>(b.getNumChannels()));
    for (int i = 0; i < b.getNumSamples(); ++i) for (int c = 0; c < b.getNumChannels(); ++c) inter[static_cast<std::size_t>(i) * static_cast<std::size_t>(b.getNumChannels()) + static_cast<std::size_t>(c)] = b.getSample(c, i);
    return sha256(inter.data(), inter.size() * sizeof(double));
}

RenderRecord LabEngine::render(const juce::AudioBuffer<double>& source, int rate, const ProductParameters& p, juce::AudioBuffer<double>& out, int block) {
    RenderRecord rec; rec.rate = rate; rec.block = block; rec.stored = p; rec.frames_in = source.getNumSamples();
    if (source.getNumChannels() != 2) { rec.error = "source must be stereo"; return rec; }
    if (!supportedRates().contains(juce::String(rate))) { rec.error = "unsupported sample rate " + juce::String(rate); return rec; }
    auto v = validateParameters(p); if (!v.ok) { rec.error = "parameters rejected: " + v.code + " " + v.detail; return rec; }
    block = juce::jlimit(1, static_cast<int>(MAX_BLOCK_LIMIT), block);
    proc_.setProcessingPrecision(juce::AudioProcessor::doublePrecision);
    proc_.prepareToPlay(rate, block);                       // (re)prepare: allocation here; host parameters pushed to the adapter
    if (!proc_.rateSupported()) { rec.error = "rate not supported by the core"; return rec; }
    applyThroughHostParameters(proc_, p);                  // candidate values through the plugin's own parameters
    proc_.prepareToPlay(rate, block);                       // same configuration = stream start: the values become the configured values (no ramp from INIT)
    rec.effective = effectiveValues(proc_); rec.latency = proc_.getLatencySamples();
    const int n = source.getNumSamples(); const int total = n + static_cast<int>(rec.latency);
    juce::AudioBuffer<double> in(2, total); in.clear(); for (int c = 0; c < 2; ++c) in.copyFrom(c, 0, source, c, 0, n);
    out.setSize(2, total, false, true, false); out.clear();
    juce::MidiBuffer midi; juce::AudioBuffer<double> blk(2, block);
    for (int done = 0; done < total; done += block) {
        const int m = juce::jmin(block, total - done); juce::AudioBuffer<double> view(blk.getArrayOfWritePointers(), 2, 0, m);
        for (int c = 0; c < 2; ++c) view.copyFrom(c, 0, in, c, done, m);
        proc_.processBlock(view, midi);
        for (int c = 0; c < 2; ++c) out.copyFrom(c, done, view, c, 0, m);
    }
    rec.frames_out = total; rec.clamps = clampReportFrom(proc_.adapter().meters());
    rec.source = analyse(source); rec.output = analyse(out); rec.source_sha256 = sha256(source); rec.output_f64_sha256 = sha256(out);
    rec.ok = true; return rec;
}

bool LabEngine::writeWav32f(const juce::File& f, const juce::AudioBuffer<double>& b, int rate) {
    f.deleteFile(); std::unique_ptr<juce::FileOutputStream> os(f.createOutputStream()); if (!os || !os->openedOk()) return false;
    juce::WavAudioFormat wav; std::unique_ptr<juce::AudioFormatWriter> w(wav.createWriterFor(os.get(), rate, static_cast<unsigned>(b.getNumChannels()), 32, {}, 0));
    if (!w) return false; os.release();
    juce::AudioBuffer<float> fb(b.getNumChannels(), b.getNumSamples()); for (int c = 0; c < b.getNumChannels(); ++c) for (int i = 0; i < b.getNumSamples(); ++i) fb.setSample(c, i, static_cast<float>(b.getSample(c, i)));
    return w->writeFromAudioSampleBuffer(fb, 0, fb.getNumSamples()) && (w.reset(), true);
}

bool LabEngine::readAudioFile(const juce::File& f, juce::AudioBuffer<double>& out, int& rate, juce::String& err) {
    juce::AudioFormatManager fm; fm.registerBasicFormats();
    std::unique_ptr<juce::AudioFormatReader> r(fm.createReaderFor(f)); if (!r) { err = "unreadable or unsupported audio file (WAV/AIFF expected)"; return false; }
    if (r->numChannels < 1 || r->numChannels > 2) { err = "mono or stereo files only"; return false; }
    if (r->lengthInSamples <= 0 || r->lengthInSamples > 60LL * 60 * 192000) { err = "empty or longer than one hour"; return false; }
    rate = static_cast<int>(std::lround(r->sampleRate));
    const int n = static_cast<int>(r->lengthInSamples);
    juce::AudioBuffer<float> fb(static_cast<int>(r->numChannels), n); r->read(&fb, 0, n, 0, true, true);
    out.setSize(2, n); for (int c = 0; c < 2; ++c) { const int src = juce::jmin(c, static_cast<int>(r->numChannels) - 1); for (int i = 0; i < n; ++i) out.setSample(c, i, static_cast<double>(fb.getSample(src, i))); }
    return true;
}

}  // namespace preset_lab
