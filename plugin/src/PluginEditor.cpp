#include "PluginEditor.h"
#include "ProductIdentity.h"
#include <cmath>

using namespace smlsp3000;
namespace id = smlsp3000::identity;

static juce::String dbText(double lin) { if (lin <= 0.0) return "-inf"; return juce::String(20.0 * std::log10(lin), 1) + " dB"; }

void PeakMeter::paint(juce::Graphics& g) {
    auto r = getLocalBounds().toFloat().reduced(1.0f);
    g.setColour(juce::Colour(0xff1c1f24)); g.fillRoundedRectangle(r, 3.0f);
    if (!available_) { g.setColour(juce::Colours::grey); g.setFont(11.0f); g.drawText("unavailable", getLocalBounds(), juce::Justification::centred); return; }
    auto toX = [&](double lin) { const double db = lin > 0.0 ? 20.0 * std::log10(lin) : -70.0; return static_cast<float>(juce::jmap(juce::jlimit(-60.0, 12.0, db), -60.0, 12.0, static_cast<double>(r.getX()), static_cast<double>(r.getRight()))); };
    g.setColour(clip_ ? juce::Colour(0xffd14b3c) : (over_ ? juce::Colour(0xffe0a030) : juce::Colour(0xff58a86c)));
    g.fillRoundedRectangle(r.withRight(toX(peak_)), 3.0f);
    g.setColour(juce::Colours::white.withAlpha(0.8f)); g.drawLine(toX(hold_), r.getY(), toX(hold_), r.getBottom(), 1.5f);
    g.setColour(juce::Colours::white.withAlpha(0.35f)); const float x0 = toX(1.0); g.drawLine(x0, r.getY(), x0, r.getBottom(), 1.0f);   // 0 dBFS reference line
    g.setColour(juce::Colours::white); g.setFont(11.0f); g.drawText(dbText(peak_), getLocalBounds().reduced(4, 0), juce::Justification::centredLeft);
}

SMLEditor::SMLEditor(SMLProcessor& p) : AudioProcessorEditor(&p), proc(p) {
    setResizable(true, true); constrainer.setSizeLimits(kMinW, kMinH, kMaxW, kMaxH); constrainer.setFixedAspectRatio(static_cast<double>(kDefW) / kDefH); setConstrainer(&constrainer);
    setSize(kDefW, kDefH);
    auto label = [&](juce::Label& l, const juce::String& text, float size, juce::Justification j = juce::Justification::centredLeft, juce::Colour c = juce::Colours::white) { l.setText(text, juce::dontSendNotification); l.setFont(juce::Font(juce::FontOptions(size))); l.setJustificationType(j); l.setColour(juce::Label::textColourId, c); addAndMakeVisible(l); };
    label(titleLabel, juce::String(id::kDisplayName) + "  v" + id::kVersion, 20.0f);
    label(claimLabel, id::kClaimBoundary, 11.5f, juce::Justification::centredLeft, juce::Colours::lightgrey);
    label(pathLabel, "SP INPUT  ->  SP ENGINE (12-bit, 26.04 kHz provisional)  ->  INTERSTAGE  ->  MPC ENGINE (18-bit ADC -> 16-bit store -> DAC, 44.1 kHz)  ->  OUTPUT", 12.5f, juce::Justification::centred, juce::Colour(0xffb9d1ff));
    for (auto* s : {&secIn, &secSp, &secInter, &secMpc, &secOut}) label(*s, "", 13.0f, juce::Justification::centred, juce::Colour(0xffe8c36a));
    secIn.setText("SP INPUT", juce::dontSendNotification); secSp.setText("SP ENGINE", juce::dontSendNotification); secInter.setText("INTERSTAGE", juce::dontSendNotification); secMpc.setText("MPC ENGINE", juce::dontSendNotification); secOut.setText("OUTPUT", juce::dontSendNotification);
    auto slider = [&](juce::Slider& s, juce::Label& l, const juce::String& name, const juce::String& tip) {
        s.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag); s.setTextBoxStyle(juce::Slider::TextBoxBelow, false, 92, 20); s.setNumDecimalPlacesToDisplay(2);   // the parameter's own text ("x.xx dB") is shown; no second suffix
        s.setTooltip(tip); s.setWantsKeyboardFocus(true); s.setTitle(name); addAndMakeVisible(s); label(l, name, 12.5f, juce::Justification::centred); };
    slider(spLevel, spLevelLabel, "SP input level", "Continuous trim at the SP input (R2), -60 to +12 dB. Ramped over 10 ms by the engine. Not a saturation control.");
    slider(interstage, interLabel, "Interstage level", "The single R10 gain between the SP output and the MPC input, -60 to +24 dB. 0 dB maps SP normalized full scale to MPC normalized full scale (owner-set software default, non-historical). Positive values can reach the MPC 18-bit converter clamp (the only overload mechanism).");
    slider(trim, trimLabel, "Output trim", "Final output gain only, -60 to +12 dB. Not a limiter; never applied to the bypassed signal.");
    auto combo = [&](juce::ComboBox& c, juce::Label& l, const juce::String& name, const juce::StringArray& items, const juce::String& tip) { c.addItemList(items, 1); c.setTooltip(tip); c.setTitle(name); addAndMakeVisible(c); label(l, name, 12.5f, juce::Justification::centred); };
    combo(spGain, spGainLabel, "SP input gain", {"0 dB", "+20 dB", "+40 dB"}, "Discrete SP input gain switch (0 / +20 / +40 dB), applied at the next block boundary without interpolation.");
    combo(mpcGain, mpcGainLabel, "MPC input gain", {"LO", "MID", "HI"}, "Discrete MPC input gain position (LO = 0 dB, MID = +20 dB, HI = +40 dB relative). Printed sensitivity labels are not full-scale calibration.");
    bypass.setTooltip("Plugin bypass: the latency-aligned original input (before every gain and both machines) replaces the processed signal with a 10 ms linear crossfade. The engine keeps running. Host bypass uses this same parameter."); bypass.setWantsKeyboardFocus(true); addAndMakeVisible(bypass);
    resetButton.setTooltip("Set the six controls to the INIT values (0 dB / 0 dB / 0 dB / LO / 0 dB / bypass off). Does not reset the audio engine."); addAndMakeVisible(resetButton);
    resetButton.onClick = [this] { for (int i = 0; i < 6; ++i) { auto* prm = proc.parameterFor(static_cast<ParamId>(i)); prm->beginChangeGesture(); prm->setValueNotifyingHost(prm->getDefaultValue()); prm->endChangeGesture(); } };
    spLevelAtt = std::make_unique<juce::SliderParameterAttachment>(*proc.parameterFor(ParamId::SP_INPUT_LEVEL_DB), spLevel);
    interAtt = std::make_unique<juce::SliderParameterAttachment>(*proc.parameterFor(ParamId::INTERSTAGE_LEVEL_DB), interstage);
    trimAtt = std::make_unique<juce::SliderParameterAttachment>(*proc.parameterFor(ParamId::OUTPUT_TRIM_DB), trim);
    spGainAtt = std::make_unique<juce::ComboBoxParameterAttachment>(*proc.parameterFor(ParamId::SP_INPUT_GAIN_DB), spGain);
    mpcGainAtt = std::make_unique<juce::ComboBoxParameterAttachment>(*proc.parameterFor(ParamId::MPC_INPUT_GAIN), mpcGain);
    bypassAtt = std::make_unique<juce::ButtonParameterAttachment>(*proc.parameterFor(ParamId::PLUGIN_BYPASS), bypass);
    for (auto* m : {&inMeterL, &inMeterR, &mpcMeterL, &mpcMeterR, &outMeterL, &outMeterR}) addAndMakeVisible(*m);
    label(inMeterLabel, "Input peak (sample peak of the host input, per block; hold line = max since last reset)", 11.0f);
    label(mpcMeterLabel, "MPC input peak (proxy-grid sample peak at the MPC core input, after the interstage gain)", 11.0f);
    label(outMeterLabel, "Output peak (sample peak after bypass/trim; amber = over-range finite output, not clamped)", 11.0f);
    label(spClipLabel, "SP 12-bit converter clamps: 0", 11.5f, juce::Justification::topLeft, juce::Colours::lightgrey); spClipLabel.setMinimumHorizontalScale(1.0f);
    label(mpcClipLabel, "MPC 18-bit converter clamps: 0   |   16-bit storage clamps: 0", 11.5f, juce::Justification::topLeft, juce::Colours::lightgrey); mpcClipLabel.setMinimumHorizontalScale(1.0f);
    label(statusLabel, "", 11.5f); label(latencyLabel, "", 11.5f); label(modelLabel, "", 11.0f, juce::Justification::centredLeft, juce::Colours::lightgrey); label(faultLabel, "", 11.5f, juce::Justification::centredLeft, juce::Colour(0xffd14b3c));
    for (auto* m : {&inMeterL, &inMeterR, &mpcMeterL, &mpcMeterR, &outMeterL, &outMeterR}) m->setTooltip("Sample-peak meter (not RMS, not LUFS, not true peak).");
    startTimerHz(24);
}

SMLEditor::~SMLEditor() { stopTimer(); }

void SMLEditor::paint(juce::Graphics& g) {
    g.fillAll(juce::Colour(0xff23272e));
    auto sec = [&](juce::Rectangle<int> r) { g.setColour(juce::Colour(0xff2d323b)); g.fillRoundedRectangle(r.toFloat(), 6.0f); g.setColour(juce::Colour(0xff454c58)); g.drawRoundedRectangle(r.toFloat(), 6.0f, 1.0f); };
    const int w = getWidth(), h = getHeight(); const int top = static_cast<int>(h * 0.22), bottom = static_cast<int>(h * 0.60);
    const int colW = (w - 40) / 5;
    for (int c = 0; c < 5; ++c) sec(juce::Rectangle<int>(20 + c * colW + 4, top, colW - 8, bottom - top));
    sec(juce::Rectangle<int>(20, bottom + 8, w - 40, h - bottom - 16));
}

void SMLEditor::resized() {
    const int w = getWidth(), h = getHeight(); const int top = static_cast<int>(h * 0.22), bottom = static_cast<int>(h * 0.60); const int colW = (w - 40) / 5;
    titleLabel.setBounds(20, 8, w / 2, 26); claimLabel.setBounds(20, 34, w - 40, 18); pathLabel.setBounds(20, 56, w - 40, 20);
    auto col = [&](int c) { return juce::Rectangle<int>(20 + c * colW + 8, top + 6, colW - 16, bottom - top - 12); };
    auto rot = [&](juce::Rectangle<int> a, juce::Label& title, juce::Label& name, juce::Slider& s) { title.setBounds(a.removeFromTop(20)); name.setBounds(a.removeFromTop(18)); s.setBounds(a.reduced(4)); };
    auto cmb = [&](juce::Rectangle<int> a, juce::Label& title, juce::Label& name, juce::ComboBox& c, juce::Component* extra) { title.setBounds(a.removeFromTop(20)); name.setBounds(a.removeFromTop(18)); c.setBounds(a.removeFromTop(26).reduced(6, 0)); if (extra) extra->setBounds(a.removeFromTop(48).reduced(2)); };
    { auto a = col(0); secIn.setBounds(a.removeFromTop(20)); auto half = a.removeFromTop(a.getHeight() / 2); spLevelLabel.setBounds(half.removeFromTop(18)); spLevel.setBounds(half.reduced(4)); spGainLabel.setBounds(a.removeFromTop(18)); spGain.setBounds(a.removeFromTop(26).reduced(6, 0)); }
    { auto a = col(1); secSp.setBounds(a.removeFromTop(20)); spClipLabel.setBounds(a); }
    { auto a = col(2); juce::Label dummy; rot(a, secInter, interLabel, interstage); }
    { auto a = col(3); secMpc.setBounds(a.removeFromTop(20)); mpcGainLabel.setBounds(a.removeFromTop(18)); mpcGain.setBounds(a.removeFromTop(26).reduced(6, 0)); mpcClipLabel.setBounds(a); }
    { auto a = col(4); secOut.setBounds(a.removeFromTop(20)); auto half = a.removeFromTop(static_cast<int>(a.getHeight() * 0.62)); trimLabel.setBounds(half.removeFromTop(18)); trim.setBounds(half.reduced(4)); bypass.setBounds(a.removeFromTop(26)); resetButton.setBounds(a.removeFromTop(26).reduced(10, 2)); }
    auto m = juce::Rectangle<int>(28, bottom + 14, w - 56, h - bottom - 28); const int rowH = juce::jmax(18, m.getHeight() / 9);
    auto meterRow = [&](juce::Label& l, PeakMeter& a, PeakMeter& b) { l.setBounds(m.removeFromTop(rowH)); auto r = m.removeFromTop(rowH); a.setBounds(r.removeFromLeft(r.getWidth() / 2).reduced(2, 2)); b.setBounds(r.reduced(2, 2)); };
    meterRow(inMeterLabel, inMeterL, inMeterR); meterRow(mpcMeterLabel, mpcMeterL, mpcMeterR); meterRow(outMeterLabel, outMeterL, outMeterR);
    auto strip = m.removeFromTop(rowH); statusLabel.setBounds(strip.removeFromLeft(strip.getWidth() / 2)); latencyLabel.setBounds(strip);
    faultLabel.setBounds(m.removeFromTop(rowH)); modelLabel.setBounds(m.removeFromTop(rowH));
}

void SMLEditor::timerCallback() {
    const auto s = proc.adapter().meters();
    const bool avail = s.prepared && proc.rateSupported();
    inMeterL.setValues(s.input_peak[0], s.input_peak_hold[0], avail); inMeterR.setValues(s.input_peak[1], s.input_peak_hold[1], avail);
    mpcMeterL.setValues(s.mpc_core_input_peak[0], s.mpc_core_input_peak[0], avail); mpcMeterR.setValues(s.mpc_core_input_peak[1], s.mpc_core_input_peak[1], avail);
    outMeterL.setValues(s.output_peak[0], s.output_peak_hold[0], avail, s.output_over_range[0]); outMeterR.setValues(s.output_peak[1], s.output_peak_hold[1], avail, s.output_over_range[1]);
    spClipLabel.setText(avail ? "SP 12-bit converter clamps (modelled code clamp): L " + juce::String(s.sp_clip[0]) + "  R " + juce::String(s.sp_clip[1]) + "\nAnalog clip: not modelled (no measurement)" : "SP clamp counter: unavailable", juce::dontSendNotification);
    mpcClipLabel.setText(avail ? "MPC 18-bit converter clamps: L " + juce::String(s.mpc_clip18[0]) + "  R " + juce::String(s.mpc_clip18[1]) + "\n16-bit storage clamps: L " + juce::String(s.mpc_clamp16[0]) + "  R " + juce::String(s.mpc_clamp16[1]) + "\nAnalog overload/recovery: not modelled" : "MPC clamp counters: unavailable", juce::dontSendNotification);
    statusLabel.setText("Status: " + proc.statusText() + (s.bypass_weight < 1.0 ? (s.bypass_weight <= 0.0 ? "  |  BYPASSED" : "  |  bypass crossfade") : ""), juce::dontSendNotification);
    latencyLabel.setText(avail ? "Reported latency: " + juce::String(static_cast<int>(s.latency)) + " samples @ " + juce::String(s.host_rate) + " Hz (" + juce::String(1000.0 * s.latency / s.host_rate, 2) + " ms); SP hold adds a frequency-dependent half period, not compensated" : "Reported latency: unavailable until prepared", juce::dontSendNotification);
    faultLabel.setText((s.nonfinite_input_samples > 0 ? "Non-finite input samples replaced by zero: " + juce::String(s.nonfinite_input_samples) + "   " : juce::String()) + (s.fault_latched ? "FAULT: internal non-finite output occurred; chunk silenced and signal state cleared (" + juce::String(s.faults) + ")" : juce::String()), juce::dontSendNotification);
    modelLabel.setText(juce::String("Model: ") + "sp1200-track-a-provisional v1 + mpc3000-track-a-provisional v1, cascade path B; native core " + NATIVE_IMPLEMENTATION_VERSION + ", adapter " + HOST_ADAPTER_VERSION + "; state schema v1; all values UNVALIDATED AGAINST HARDWARE", juce::dontSendNotification);
}
