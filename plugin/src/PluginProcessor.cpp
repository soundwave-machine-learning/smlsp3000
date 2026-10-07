#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "ProductIdentity.h"
#include "track_a_assets_v1.hpp"

using namespace smlsp3000;
namespace A = smlsp3000::assets_v1;
namespace id = smlsp3000::identity;

static juce::NormalisableRange<float> dbRange(double lo, double hi) { return juce::NormalisableRange<float>(static_cast<float>(lo), static_cast<float>(hi), 0.0f); }   // linear in dB, no step quantisation

SMLProcessor::SMLProcessor()
    : AudioProcessor(BusesProperties().withInput("Input", juce::AudioChannelSet::stereo(), true).withOutput("Output", juce::AudioChannelSet::stereo(), true)) {
    auto fmtDb = [](float v, int) { return juce::String(v, 2) + " dB"; };
    auto spLevel = std::make_unique<juce::AudioParameterFloat>(juce::ParameterID{"sp_input_level_db", 1}, "SP Input Level", dbRange(A::CTRL_SP_INPUT_LEVEL_DB_MIN, A::CTRL_SP_INPUT_LEVEL_DB_MAX), static_cast<float>(A::CTRL_SP_INPUT_LEVEL_DB_DEFAULT), juce::AudioParameterFloatAttributes().withLabel("dB").withStringFromValueFunction(fmtDb));
    auto spGain = std::make_unique<juce::AudioParameterChoice>(juce::ParameterID{"sp_input_gain", 1}, "SP Input Gain", juce::StringArray{"0 dB", "+20 dB", "+40 dB"}, 0);
    auto inter = std::make_unique<juce::AudioParameterFloat>(juce::ParameterID{"interstage_level_db", 1}, "Interstage Level", dbRange(A::PRODUCT_INTERSTAGE_RESEARCH_MIN_DB, A::PRODUCT_INTERSTAGE_RESEARCH_MAX_DB), static_cast<float>(A::PRODUCT_INTERSTAGE_DEFAULT_DB), juce::AudioParameterFloatAttributes().withLabel("dB").withStringFromValueFunction(fmtDb));
    auto mpcGain = std::make_unique<juce::AudioParameterChoice>(juce::ParameterID{"mpc_input_gain", 1}, "MPC Input Gain", juce::StringArray{"LO", "MID", "HI"}, 0);
    auto trim = std::make_unique<juce::AudioParameterFloat>(juce::ParameterID{"output_trim_db", 1}, "Output Trim", dbRange(A::CTRL_OUTPUT_TRIM_DB_MIN, A::CTRL_OUTPUT_TRIM_DB_MAX), static_cast<float>(A::CTRL_OUTPUT_TRIM_DB_DEFAULT), juce::AudioParameterFloatAttributes().withLabel("dB").withStringFromValueFunction(fmtDb));
    auto byp = std::make_unique<juce::AudioParameterBool>(juce::ParameterID{"plugin_bypass", 1}, "Bypass", A::CTRL_PLUGIN_BYPASS_DEFAULT);
    params_[0] = spLevel.get(); params_[1] = spGain.get(); params_[2] = inter.get(); params_[3] = mpcGain.get(); params_[4] = trim.get(); params_[5] = byp.get(); bypassParam = byp.get();
    addParameter(spLevel.release()); addParameter(spGain.release()); addParameter(inter.release()); addParameter(mpcGain.release()); addParameter(trim.release()); addParameter(byp.release());
    for (auto* p : params_) p->addListener(this);
}

SMLProcessor::~SMLProcessor() { for (auto* p : params_) p->removeListener(this); }

const juce::String SMLProcessor::getName() const { return id::kDisplayName; }

bool SMLProcessor::isBusesLayoutSupported(const BusesLayout& layouts) const {
    return layouts.getMainInputChannelSet() == juce::AudioChannelSet::stereo() && layouts.getMainOutputChannelSet() == juce::AudioChannelSet::stereo();
}

void SMLProcessor::pushParameterToAdapter(int i) {
    double v = 0.0;
    switch (i) {
        case 0: v = static_cast<juce::AudioParameterFloat*>(params_[0])->get(); break;
        case 1: v = A::SP_INPUT_GAIN_STEPS_DB[static_cast<juce::AudioParameterChoice*>(params_[1])->getIndex()]; break;
        case 2: v = static_cast<juce::AudioParameterFloat*>(params_[2])->get(); break;
        case 3: v = static_cast<juce::AudioParameterChoice*>(params_[3])->getIndex(); break;
        case 4: v = static_cast<juce::AudioParameterFloat*>(params_[4])->get(); break;
        default: v = static_cast<juce::AudioParameterBool*>(params_[5])->get() ? 1.0 : 0.0; break;
    }
    adapter_.set_parameter(static_cast<ParamId>(i), v);     // block-boundary delivery: the adapter applies it at the next block start
}

void SMLProcessor::parameterValueChanged(int parameterIndex, float) { pushParameterToAdapter(parameterIndex); }

void SMLProcessor::prepareToPlay(double sampleRate, int samplesPerBlock) {
    const int rate = static_cast<int>(std::lround(sampleRate));
    const std::size_t maxBlock = static_cast<std::size_t>(juce::jlimit(1, static_cast<int>(MAX_BLOCK_LIMIT), samplesPerBlock));
    ProductParameters p = ProductParameters::defaults();
    p.sp_input_level_db = adapter_.parameter(ParamId::SP_INPUT_LEVEL_DB); p.sp_input_gain_db = static_cast<int>(adapter_.parameter(ParamId::SP_INPUT_GAIN_DB));
    p.interstage_level_db = adapter_.parameter(ParamId::INTERSTAGE_LEVEL_DB); p.mpc_input_gain = static_cast<MpcInputGain>(static_cast<int>(adapter_.parameter(ParamId::MPC_INPUT_GAIN)));
    p.output_trim_db = adapter_.parameter(ParamId::OUTPUT_TRIM_DB); p.plugin_bypass = adapter_.parameter(ParamId::PLUGIN_BYPASS) != 0.0;
    if (!adapter_.prepared() || rate != static_cast<int>(currentRate_.load()) || static_cast<int>(maxBlock) != preparedBlock_.load()) {
        for (int i = 0; i < 6; ++i) pushParameterToAdapter(i);     // the host may have set parameters before prepare
        p.sp_input_level_db = adapter_.parameter(ParamId::SP_INPUT_LEVEL_DB); p.sp_input_gain_db = static_cast<int>(adapter_.parameter(ParamId::SP_INPUT_GAIN_DB));
        p.interstage_level_db = adapter_.parameter(ParamId::INTERSTAGE_LEVEL_DB); p.mpc_input_gain = static_cast<MpcInputGain>(static_cast<int>(adapter_.parameter(ParamId::MPC_INPUT_GAIN)));
        p.output_trim_db = adapter_.parameter(ParamId::OUTPUT_TRIM_DB); p.plugin_bypass = adapter_.parameter(ParamId::PLUGIN_BYPASS) != 0.0;
        auto r = adapter_.prepare(rate, maxBlock, p, nullptr);       // (re)prepare: allocation happens here, never in processBlock
        rateSupported_.store(r.ok); currentRate_.store(sampleRate); preparedBlock_.store(static_cast<int>(maxBlock));
    } else {
        adapter_.reset();                                            // same configuration: stream start (deterministic from reset)
    }
    setLatencySamples(static_cast<int>(adapter_.latency()));
}

void SMLProcessor::reset() { adapter_.reset(); }

void SMLProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer&) {
    // No juce::ScopedNoDenormals here: the core's floating-point environment (no FTZ/DAZ) is part of its validated numeric contract (OWN-DEC-035).
    const float* in[2] = {buffer.getReadPointer(0), buffer.getReadPointer(1)}; float* out[2] = {buffer.getWritePointer(0), buffer.getWritePointer(1)};
    adapter_.process(in, out, static_cast<std::size_t>(buffer.getNumSamples()));
}
void SMLProcessor::processBlock(juce::AudioBuffer<double>& buffer, juce::MidiBuffer&) {
    const double* in[2] = {buffer.getReadPointer(0), buffer.getReadPointer(1)}; double* out[2] = {buffer.getWritePointer(0), buffer.getWritePointer(1)};
    adapter_.process(in, out, static_cast<std::size_t>(buffer.getNumSamples()));
}
// Hosts that bypass through the bypass parameter never call these; hosts that do get the SAME mechanism (parameter → crossfade).
void SMLProcessor::processBlockBypassed(juce::AudioBuffer<float>& b, juce::MidiBuffer& m) { adapter_.set_parameter(ParamId::PLUGIN_BYPASS, 1.0); processBlock(b, m); }
void SMLProcessor::processBlockBypassed(juce::AudioBuffer<double>& b, juce::MidiBuffer& m) { adapter_.set_parameter(ParamId::PLUGIN_BYPASS, 1.0); processBlock(b, m); }

juce::AudioProcessorEditor* SMLProcessor::createEditor() { ++editorOpens; return new SMLEditor(*this); }

void SMLProcessor::getStateInformation(juce::MemoryBlock& destData) {
    const juce::SpinLock::ScopedLockType sl(stateLock_);
    juce::XmlElement root(id::kStateRootTag);
    root.setAttribute("schema_version", 1); root.setAttribute("adapter", HOST_ADAPTER_VERSION); root.setAttribute("product_version", id::kVersion);
    root.createNewChildElement("native")->addTextElement(adapter_.save_state());
    copyXmlToBinary(root, destData);
}

void SMLProcessor::setStateInformation(const void* data, int sizeInBytes) {
    const juce::SpinLock::ScopedLockType sl(stateLock_);
    if (sizeInBytes <= 0 || sizeInBytes > 1024 * 1024) return;                       // bounded: oversized blobs are rejected untouched
    std::unique_ptr<juce::XmlElement> xml(getXmlFromBinary(data, sizeInBytes));
    if (!xml || !xml->hasTagName(id::kStateRootTag)) return;                       // not our state: nothing applied
    if (xml->getIntAttribute("schema_version", -1) != 1) return;                   // future/unknown wrapper schema: rejected explicitly
    auto* native = xml->getChildByName("native");
    if (!native) return;
    const juce::String text = native->getAllSubText();
    auto r = adapter_.load_state(text.toStdString());                               // validated off the audio thread; published lock-free
    if (!r.ok) return;                                                             // core rejection codes: nothing applied
    syncParametersFromAdapter();
}

void SMLProcessor::syncParametersFromAdapter() {
    auto setF = [&](int i, ParamId pid) { auto* p = static_cast<juce::AudioParameterFloat*>(params_[i]); const float v = static_cast<float>(adapter_.parameter(pid)); p->setValueNotifyingHost(p->convertTo0to1(v)); };
    setF(0, ParamId::SP_INPUT_LEVEL_DB); setF(2, ParamId::INTERSTAGE_LEVEL_DB); setF(4, ParamId::OUTPUT_TRIM_DB);
    { auto* p = static_cast<juce::AudioParameterChoice*>(params_[1]); const int db = static_cast<int>(adapter_.parameter(ParamId::SP_INPUT_GAIN_DB)); int idx = 0; for (int k = 0; k < 3; ++k) if (A::SP_INPUT_GAIN_STEPS_DB[k] == db) idx = k; p->setValueNotifyingHost(p->convertTo0to1(static_cast<float>(idx))); }
    { auto* p = static_cast<juce::AudioParameterChoice*>(params_[3]); p->setValueNotifyingHost(p->convertTo0to1(static_cast<float>(adapter_.parameter(ParamId::MPC_INPUT_GAIN)))); }
    { auto* p = static_cast<juce::AudioParameterBool*>(params_[5]); p->setValueNotifyingHost(adapter_.parameter(ParamId::PLUGIN_BYPASS) != 0.0 ? 1.0f : 0.0f); }
}

juce::String SMLProcessor::statusText() const {
    if (!adapter_.prepared()) return "not prepared (editor opened before audio preparation)";
    if (!rateSupported_.load()) return "unsupported sample rate: output muted";
    return "ready";
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new SMLProcessor(); }
