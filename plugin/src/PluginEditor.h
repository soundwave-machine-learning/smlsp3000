// SML SP-3000 editor (Sprint 7, OWN-DEC-033): original functional layout showing the actual path
// SP INPUT → SP ENGINE → INTERSTAGE → MPC ENGINE → OUTPUT with the six frozen controls, honest meters and a status strip.
// No fake animation; unavailable meters say so; the over-range indicator never alters audio. Prototype pending owner G-10 review.
#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>
#include "PluginProcessor.h"

class PeakMeter : public juce::Component, public juce::SettableTooltipClient {
public:
    void setValues(double peak, double hold, bool available, bool overRange = false, bool clip = false) { peak_ = peak; hold_ = hold; available_ = available; over_ = overRange; clip_ = clip; repaint(); }
    void paint(juce::Graphics& g) override;
private:
    double peak_ = 0.0, hold_ = 0.0; bool available_ = false, over_ = false, clip_ = false;
};

class SMLEditor : public juce::AudioProcessorEditor, private juce::Timer {
public:
    explicit SMLEditor(SMLProcessor&);
    ~SMLEditor() override;
    void paint(juce::Graphics&) override;
    void resized() override;
    static constexpr int kMinW = 760, kMinH = 440, kDefW = 920, kDefH = 540, kMaxW = 1520, kMaxH = 880;
private:
    void timerCallback() override;
    void layoutSection(juce::Rectangle<int> area, juce::Label& title, std::initializer_list<juce::Component*> items);
    SMLProcessor& proc;
    juce::TooltipWindow tooltips{this, 400};
    juce::Label titleLabel, claimLabel, pathLabel, statusLabel, latencyLabel, modelLabel, faultLabel;
    juce::Label secIn, secSp, secInter, secMpc, secOut;
    juce::Slider spLevel, interstage, trim;
    juce::ComboBox spGain, mpcGain;
    juce::ToggleButton bypass{"Bypass (latency-aligned dry, 10 ms crossfade)"};
    juce::TextButton resetButton{"Reset to INIT"};
    juce::Label spLevelLabel, interLabel, trimLabel, spGainLabel, mpcGainLabel;
    PeakMeter inMeterL, inMeterR, mpcMeterL, mpcMeterR, outMeterL, outMeterR;
    juce::Label inMeterLabel, mpcMeterLabel, outMeterLabel, spClipLabel, mpcClipLabel;
    std::unique_ptr<juce::SliderParameterAttachment> spLevelAtt, interAtt, trimAtt;
    std::unique_ptr<juce::ComboBoxParameterAttachment> spGainAtt, mpcGainAtt;
    std::unique_ptr<juce::ButtonParameterAttachment> bypassAtt;
    juce::ComponentBoundsConstrainer constrainer;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SMLEditor)
};
