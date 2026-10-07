// SML SP-3000 — JUCE AudioProcessor shell around the framework-independent HostAdapter (Sprint 7).
// All sound is the unchanged Sprint 6 native core. This file only bridges parameters, state, latency and buffers.
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <atomic>
#include "smlsp3000/host_adapter.hpp"

class SMLProcessor : public juce::AudioProcessor, private juce::AudioProcessorParameter::Listener {
public:
    SMLProcessor();
    ~SMLProcessor() override;
    // ---- lifecycle
    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    void reset() override;
    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;
    // ---- audio
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    void processBlock(juce::AudioBuffer<double>&, juce::MidiBuffer&) override;
    void processBlockBypassed(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    void processBlockBypassed(juce::AudioBuffer<double>&, juce::MidiBuffer&) override;
    bool supportsDoublePrecisionProcessing() const override { return true; }
    juce::AudioProcessorParameter* getBypassParameter() const override { return bypassParam; }
    // ---- editor
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }
    // ---- identity
    const juce::String getName() const override;
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return "INIT"; }
    void changeProgramName(int, const juce::String&) override {}
    // ---- state (message thread)
    void getStateInformation(juce::MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;
    // ---- for the editor
    smlsp3000::HostAdapter& adapter() { return adapter_; }
    juce::String statusText() const;
    juce::RangedAudioParameter* parameterFor(smlsp3000::ParamId id) const { return params_[static_cast<int>(id)]; }
    bool rateSupported() const { return rateSupported_.load(); }
    double currentRate() const { return currentRate_.load(); }
    std::atomic<int> editorOpens{0};
private:
    void parameterValueChanged(int parameterIndex, float newValue) override;
    void parameterGestureChanged(int, bool) override {}
    void pushParameterToAdapter(int index);
    void syncParametersFromAdapter();
    smlsp3000::HostAdapter adapter_;
    juce::RangedAudioParameter* params_[6]{};
    juce::AudioParameterBool* bypassParam = nullptr;
    std::atomic<bool> rateSupported_{false}; std::atomic<double> currentRate_{0.0}; std::atomic<int> preparedBlock_{0};
    juce::SpinLock stateLock_;   // message-thread-only serialisation of set/getStateInformation (never touched by processBlock)
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SMLProcessor)
};
