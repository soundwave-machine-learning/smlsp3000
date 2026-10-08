// SML SP-3000 Preset Lab - development/authoring tool (NOT the shipped plugin). Loads reference beats, auditions the exact
// product processor (SMLProcessor -> HostAdapter -> native core) with the six product controls, A/B and processed-vs-bypass
// comparison, candidate metadata, deterministic audition renders with clamp reports, telemetry, candidate files and manifests.
// Headless modes (for tests/screenshots):  --validate f.json | --roundtrip in.json out.json | --init-state |
//   --render <candidate.json|INIT> <source.wav> <out_dir> [--block N] | --snapshot <out_dir> <source.wav> [cand.json ...]
#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_audio_utils/juce_audio_utils.h>
#include <juce_gui_basics/juce_gui_basics.h>
#include <cmath>
#include <cstdio>
#include <optional>
#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "ProductIdentity.h"
#include "PresetCandidate.h"
#include "LabEngine.h"

using namespace preset_lab;
using namespace smlsp3000;
#ifndef SMLSP3000_REPO_ROOT
#define SMLSP3000_REPO_ROOT "."
#endif
#ifndef SMLSP3000_LAB_BUILD_ID
#define SMLSP3000_LAB_BUILD_ID "unknown"
#endif

static juce::String dbs(double lin) { return lin <= 0.0 ? juce::String("-inf dB") : juce::String(20.0 * std::log10(lin), 2) + " dB"; }
static juce::File repoRoot() { return juce::File(SMLSP3000_REPO_ROOT); }
static juce::File candidatesDir() { return repoRoot().getChildFile("presets").getChildFile("candidates"); }
static juce::File rendersDir() { return repoRoot().getChildFile("reference").getChildFile("preset_lab").getChildFile("renders"); }

struct Source { juce::File file; juce::AudioBuffer<double> audio; int rate = 0; FileAnalysis analysis; juce::String sha256; };

// ---------------------------------------------------------------- live audition path: transport -> product processor -> monitor trim
class LiveSource : public juce::AudioSource {
public:
    explicit LiveSource(SMLProcessor& p) : proc(p) {}
    void prepareToPlay(int block, double rate) override { transport.prepareToPlay(block, rate); proc.setProcessingPrecision(juce::AudioProcessor::singlePrecision); proc.prepareToPlay(rate, block); deviceRate = rate; }
    void releaseResources() override { transport.releaseResources(); proc.releaseResources(); }
    void getNextAudioBlock(const juce::AudioSourceChannelInfo& info) override {
        transport.getNextAudioBlock(info);
        if (info.buffer->getNumChannels() < 2) { info.clearActiveBufferRegion(); return; }
        juce::AudioBuffer<float> view(info.buffer->getArrayOfWritePointers(), 2, info.startSample, info.numSamples);
        juce::MidiBuffer midi; proc.processBlock(view, midi);                              // the product path; nothing else touches the audio
        const float g = monitorGain.load(); if (g != 1.0f) view.applyGain(g);          // AUDITION-ONLY monitor trim (never saved, never part of a preset)
    }
    juce::AudioTransportSource transport; std::atomic<float> monitorGain{1.0f}; double deviceRate = 0.0;
private:
    SMLProcessor& proc;
};

// ---------------------------------------------------------------- main component
class LabComponent : public juce::Component, private juce::Timer, private juce::ListBoxModel {
public:
    LabComponent() : live(liveProc) {
        formats.registerBasicFormats();
        auto lbl = [&](juce::Label& l, const juce::String& t, float sz, juce::Colour c = juce::Colours::white, juce::Justification j = juce::Justification::centredLeft) { l.setText(t, juce::dontSendNotification); l.setFont(juce::Font(juce::FontOptions(sz))); l.setColour(juce::Label::textColourId, c); l.setJustificationType(j); addAndMakeVisible(l); };
        lbl(title, "SML SP-3000 PRESET LAB  (development authoring tool - not the shipped plugin; product DSP unchanged)", 17.0f, juce::Colour(0xffe8c36a));
        lbl(claim, identity::kClaimBoundary, 11.0f, juce::Colours::lightgrey);
        for (auto* s : {&secSource, &secCandidate, &secMeta, &secTelemetry}) lbl(*s, "", 13.0f, juce::Colour(0xffe8c36a), juce::Justification::centred);
        secSource.setText("SOURCE MATERIAL", juce::dontSendNotification); secCandidate.setText("CANDIDATE - the six product controls", juce::dontSendNotification); secMeta.setText("CANDIDATE METADATA", juce::dontSendNotification); secTelemetry.setText("TELEMETRY (live processor; sample peaks, modelled clamp counts)", juce::dontSendNotification);
        // sources
        sourceList.setModel(this); addAndMakeVisible(sourceList);
        for (auto* b : {&loadSourceBtn, &removeSourceBtn, &playBtn, &stopBtn, &audioSettingsBtn, &renderBtn, &compareBtn, &newBtn, &openBtn, &saveRevBtn, &overwriteBtn, &exportManifestBtn, &resetBtn, &aBtn, &bBtn, &bInitBtn, &copyABBtn, &bypassCmpBtn, &helpBtn, &aboutBtn}) addAndMakeVisible(*b);
        loadSourceBtn.onClick = [this] { chooseSource(); }; removeSourceBtn.onClick = [this] { removeSource(); };
        playBtn.onClick = [this] { play(); }; stopBtn.onClick = [this] { live.transport.stop(); };
        loopToggle.setToggleState(true, juce::dontSendNotification); addAndMakeVisible(loopToggle); loopToggle.onClick = [this] { if (reader) reader->setLooping(loopToggle.getToggleState()); };
        audioSettingsBtn.onClick = [this] { openAudioSettings(); };
        lbl(sourceInfo, "no source loaded", 11.0f, juce::Colours::lightgrey); lbl(deviceInfo, "", 11.0f, juce::Colours::lightgrey);
        // controls (bound to the live processor's host parameters: the plugin's own mapping)
        auto rot = [&](juce::Slider& s, juce::Label& l, const juce::String& name, ParamId id) { s.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag); s.setTextBoxStyle(juce::Slider::TextBoxBelow, false, 90, 20); s.setNumDecimalPlacesToDisplay(2); addAndMakeVisible(s); lbl(l, name, 12.0f, juce::Colours::white, juce::Justification::centred); return std::make_unique<juce::SliderParameterAttachment>(*liveProc.parameterFor(id), s); };
        spLevelAtt = rot(spLevel, spLevelLbl, "SP input level (dB)", ParamId::SP_INPUT_LEVEL_DB); interAtt = rot(interstage, interLbl, "Interstage level (dB)", ParamId::INTERSTAGE_LEVEL_DB); trimAtt = rot(trim, trimLbl, "Output trim (dB)", ParamId::OUTPUT_TRIM_DB);
        auto cmb = [&](juce::ComboBox& c, juce::Label& l, const juce::String& name, const juce::StringArray& items, ParamId id) { c.addItemList(items, 1); addAndMakeVisible(c); lbl(l, name, 12.0f, juce::Colours::white, juce::Justification::centred); return std::make_unique<juce::ComboBoxParameterAttachment>(*liveProc.parameterFor(id), c); };
        spGainAtt = cmb(spGain, spGainLbl, "SP input gain", {"0 dB", "+20 dB", "+40 dB"}, ParamId::SP_INPUT_GAIN_DB); mpcGainAtt = cmb(mpcGain, mpcGainLbl, "MPC input gain", {"LO", "MID", "HI"}, ParamId::MPC_INPUT_GAIN);
        addAndMakeVisible(bypassToggle); bypassAtt = std::make_unique<juce::ButtonParameterAttachment>(*liveProc.parameterFor(ParamId::PLUGIN_BYPASS), bypassToggle);
        resetBtn.onClick = [this] { applyToLive(ProductParameters::defaults()); };
        aBtn.onClick = [this] { selectAB(false); }; bBtn.onClick = [this] { selectAB(true); }; bInitBtn.onClick = [this] { bParams = ProductParameters::defaults(); if (listeningToB) applyToLive(bParams); refreshStatus(); };
        copyABBtn.onClick = [this] { bParams = currentParams(); refreshStatus(); };
        bypassCmpBtn.onClick = [this] { auto* p = liveProc.parameterFor(ParamId::PLUGIN_BYPASS); p->setValueNotifyingHost(p->getValue() > 0.5f ? 0.0f : 1.0f); };
        monitorTrim.setSliderStyle(juce::Slider::LinearHorizontal); monitorTrim.setRange(-24.0, 12.0, 0.1); monitorTrim.setValue(0.0); monitorTrim.setTextBoxStyle(juce::Slider::TextBoxRight, false, 70, 18); monitorTrim.setTextValueSuffix(" dB"); addAndMakeVisible(monitorTrim);
        monitorTrim.onValueChange = [this] { live.monitorGain.store(static_cast<float>(std::pow(10.0, monitorTrim.getValue() / 20.0))); };
        lbl(monitorLbl, "AUDITION MONITOR TRIM - playback only, after the processor; never saved, not part of any preset", 10.5f, juce::Colour(0xffe0a030));
        lbl(abStatus, "", 11.5f, juce::Colours::white); lbl(candStatus, "", 12.5f, juce::Colour(0xffb9d1ff));
        // metadata
        auto edit = [&](juce::TextEditor& e, juce::Label& l, const juce::String& name, bool multi) { e.setMultiLine(multi); e.setReturnKeyStartsNewLine(multi); e.setScrollbarsShown(multi); addAndMakeVisible(e); lbl(l, name, 11.0f, juce::Colours::lightgrey); e.onTextChange = [this] { refreshStatus(); }; };
        edit(nameEd, nameLbl, "Name", false); edit(authorEd, authorLbl, "Author", false); edit(descEd, descLbl, "Description", true); edit(notesEd, notesLbl, "Audition notes", true); edit(clampObsEd, clampObsLbl, "Clamp observations", true); edit(engEd, engLbl, "Engineering note (optional)", true); edit(sourcesEd, sourcesLbl, "Source material used (one per line)", true);
        categoryBox.addItemList(categories(), 1); categoryBox.setSelectedId(categories().indexOf("EXPERIMENTAL") + 1, juce::dontSendNotification); addAndMakeVisible(categoryBox); lbl(categoryLbl, "Category (authoring only; no category implies hardware authenticity)", 11.0f, juce::Colours::lightgrey); categoryBox.onChange = [this] { refreshStatus(); };
        statusBox.addItemList(acceptanceStatuses(), 1); statusBox.setSelectedId(1, juce::dontSendNotification); addAndMakeVisible(statusBox); lbl(statusLbl, "Acceptance status", 11.0f, juce::Colours::lightgrey); statusBox.onChange = [this] { refreshStatus(); };
        lbl(idLbl, "", 11.0f, juce::Colours::lightgrey);
        newBtn.onClick = [this] { newCandidate(); }; openBtn.onClick = [this] { chooseCandidate(); }; saveRevBtn.onClick = [this] { save(false); }; overwriteBtn.onClick = [this] { save(true); }; exportManifestBtn.onClick = [this] { exportManifest(); };
        renderBtn.onClick = [this] { renderCurrent(); }; compareBtn.onClick = [this] { compareAB(); };
        helpBtn.onClick = [this] { openManual(); }; aboutBtn.onClick = [this] { juce::AlertWindow::showMessageBoxAsync(juce::MessageBoxIconType::InfoIcon, "SML SP-3000 Preset Lab", juce::String(TOOL_VERSION) + "\nProduct: " + identity::kDisplayName + " v" + identity::kVersion + "\nNative core: " + NATIVE_IMPLEMENTATION_VERSION + "\nAdapter: " + HOST_ADAPTER_VERSION + "\n\n" + identity::kClaimBoundary + "\n\nThe lab uses the product processor itself; it adds no DSP, no limiter, no normalisation, no hidden controls. Manual: docs/SML_SP3000_MANUAL.md"); };
        // telemetry
        for (auto* m : {&inL, &inR, &mpcL, &mpcR, &outL, &outR}) addAndMakeVisible(*m);
        lbl(inLbl, "INPUT peak / hold (sample peak of the host input)", 10.5f, juce::Colours::lightgrey); lbl(mpcLbl, "MPC INPUT proxy peak (proxy-grid sample peak at the MPC core input, after the interstage gain)", 10.5f, juce::Colours::lightgrey); lbl(outLbl, "OUTPUT peak / hold (after bypass/trim; amber = finite over-range, not clamped)", 10.5f, juce::Colours::lightgrey);
        lbl(countersLbl, "", 11.5f, juce::Colours::white); lbl(rateLbl, "", 11.0f, juce::Colours::lightgrey);
        reportEd.setMultiLine(true); reportEd.setReadOnly(true); reportEd.setFont(juce::Font(juce::FontOptions(juce::Font::getDefaultMonospacedFontName(), 11.5f, juce::Font::plain))); reportEd.setText("No audition render yet. Render writes a 32-bit float WAV plus a render record (hashes, parameters, clamp report) under reference/preset_lab/renders/."); addAndMakeVisible(reportEd);
        for (auto* p : liveParams()) p->addListener(&paramWatch); paramWatch.onChange = [this] { refreshStatus(); };
        newCandidate();
        const juce::String err = devices.initialise(0, 2, nullptr, true);
        deviceInfo.setText(err.isEmpty() ? (devices.getCurrentAudioDevice() ? "audio device: " + devices.getCurrentAudioDevice()->getName() : "no audio output device (renders and screenshots still work)") : "audio: " + err, juce::dontSendNotification);
        player.setSource(&live); devices.addAudioCallback(&player);
        setSize(1280, 820); startTimerHz(20);
    }
    ~LabComponent() override { stopTimer(); devices.removeAudioCallback(&player); player.setSource(nullptr); live.transport.setSource(nullptr); for (auto* p : liveParams()) p->removeListener(&paramWatch); }

    // ---- public for the headless modes
    bool addSource(const juce::File& f, juce::String& err) {
        Source s; s.file = f; if (!LabEngine::readAudioFile(f, s.audio, s.rate, err)) return false;
        s.analysis = analyse(s.audio); s.sha256 = LabEngine::sha256(s.audio); sources.push_back(std::move(s)); sourceList.updateContent(); sourceList.selectRow(static_cast<int>(sources.size()) - 1); refreshSourceInfo(); return true;
    }
    bool loadCandidate(const juce::File& f, juce::String& err) {
        Candidate c; auto r = loadCandidateFile(f, c); if (!r.ok) { err = r.code + ": " + r.detail; return false; }
        loaded = c; loadedFile = f; current = c; applyToLive(c.params); metaToUi(c); baseline = serializeCandidate(uiToCandidate()); refreshStatus(); return true;
    }
    RenderRecord renderCurrent(juce::File* outFileOut = nullptr) {
        RenderRecord rec; if (sources.empty()) { reportEd.setText("Load a source first."); return rec; }
        const Source& src = sources[static_cast<std::size_t>(juce::jlimit(0, static_cast<int>(sources.size()) - 1, sourceList.getSelectedRow()))];
        Candidate c = uiToCandidate(); juce::AudioBuffer<double> out;
        rec = renderEngine.render(src.audio, src.rate, c.params, out); rec.candidate_id = c.id; rec.candidate_revision = c.revision;
        if (!rec.ok) { reportEd.setText("Render failed: " + rec.error); return rec; }
        const juce::File dir = rendersDir().getChildFile(c.id + "_r" + juce::String(c.revision)); dir.createDirectory();
        const juce::String base = src.file.getFileNameWithoutExtension() + "_" + juce::String(src.rate); const juce::File wav = dir.getChildFile(base + ".wav"), js = dir.getChildFile(base + ".render.json");
        if (!LabEngine::writeWav32f(wav, out, src.rate)) { reportEd.setText("Render failed: cannot write " + wav.getFullPathName()); rec.ok = false; return rec; }
        { juce::MemoryBlock mb; wav.loadFileAsData(mb); rec.output_file_sha256 = LabEngine::sha256(mb.getData(), mb.getSize()); }
        js.replaceWithText(juce::JSON::toString(rec.toVar(SMLSP3000_LAB_BUILD_ID, src.file.getFullPathName(), wav.getFullPathName()), false) + "\n");
        lastReport = "Audition render: " + c.name + " (" + c.id + " r" + juce::String(c.revision) + ") on " + src.file.getFileName() + " @ " + juce::String(src.rate) + " Hz, latency " + juce::String(rec.latency) + "\n" + rec.clamps.text()
            + "Source sample peak L/R: " + dbs(rec.source.peak[0]) + " / " + dbs(rec.source.peak[1]) + "   RMS: " + dbs(rec.source.rms[0]) + " / " + dbs(rec.source.rms[1]) + "\n"
            + "Output sample peak L/R: " + dbs(rec.output.peak[0]) + " / " + dbs(rec.output.peak[1]) + "   RMS: " + dbs(rec.output.rms[0]) + " / " + dbs(rec.output.rms[1]) + "   (offline file analysis, audition-only level information; not a plugin meter, not LUFS, not true peak)\n"
            + "Written: " + wav.getFullPathName() + "\nRecord: " + js.getFullPathName() + "\noutput_f64_sha256 " + rec.output_f64_sha256;
        reportEd.setText(lastReport);
        current.meta.input_peak = juce::jmax(rec.source.peak[0], rec.source.peak[1]); current.meta.output_peak = juce::jmax(rec.output.peak[0], rec.output.peak[1]);
        if (clampObsEd.getText().trim().isEmpty()) clampObsEd.setText(rec.clamps.text().trim(), juce::dontSendNotification);
        if (!sourcesEd.getText().contains(src.file.getFileName())) sourcesEd.setText((sourcesEd.getText().trim() + "\n" + src.file.getFileName() + " (sha256 " + src.sha256.substring(0, 16) + ")").trim(), juce::dontSendNotification);
        if (devices.getCurrentAudioDevice() == nullptr) feedLiveOffline(src);   // no audio device: the telemetry panel shows an offline pass of the same source through the live processor
        if (outFileOut) *outFileOut = wav; refreshStatus(); return rec;
    }
    void feedLiveOffline(const Source& src) {
        const int block = 512; liveProc.setProcessingPrecision(juce::AudioProcessor::singlePrecision); liveProc.prepareToPlay(src.rate, block);
        juce::AudioBuffer<float> blk(2, block); juce::MidiBuffer midi; const int n = src.audio.getNumSamples();
        for (int done = 0; done < n; done += block) { const int m = juce::jmin(block, n - done); juce::AudioBuffer<float> view(blk.getArrayOfWritePointers(), 2, 0, m); for (int c = 0; c < 2; ++c) for (int i = 0; i < m; ++i) view.setSample(c, i, static_cast<float>(src.audio.getSample(c, done + i))); liveProc.processBlock(view, midi); }
        telemetryNote = "telemetry: offline pass of " + src.file.getFileName() + " through the live processor (no audio device open)";
    }
    Candidate uiToCandidate() {
        Candidate c = current; c.params = currentParams(); c.name = nameEd.getText().trim(); c.category = categoryBox.getText(); c.meta.author = authorEd.getText(); c.meta.description = descEd.getText(); c.meta.audition_notes = notesEd.getText(); c.meta.clamp_observations = clampObsEd.getText(); c.meta.engineering_note = engEd.getText();
        c.meta.source_material.clear(); for (auto& l : juce::StringArray::fromLines(sourcesEd.getText())) if (l.trim().isNotEmpty()) c.meta.source_material.add(l.trim());
        c.meta.acceptance_status = statusBox.getText(); return c;
    }
    void setModifiedForDemo() { notesEd.setText(notesEd.getText() + "\n(edited after load - demonstration of the MODIFIED state)"); refreshStatus(); }
    void setDemoRenderReport(const juce::String& s) { reportEd.setText(s); }

private:
    juce::Array<juce::RangedAudioParameter*> liveParams() { juce::Array<juce::RangedAudioParameter*> a; for (int i = 0; i < 6; ++i) a.add(liveProc.parameterFor(static_cast<ParamId>(i))); return a; }
    ProductParameters currentParams() const { return LabEngine::readBackFromAdapter(liveProc); }
    void applyToLive(const ProductParameters& p) { LabEngine::applyThroughHostParameters(liveProc, p); refreshStatus(); }
    void selectAB(bool toB) { if (toB == listeningToB) return; if (toB) { aParams = currentParams(); listeningToB = true; applyToLive(bParams); } else { bParams = currentParams(); listeningToB = false; applyToLive(aParams); } refreshStatus(); }
    void newCandidate() { Candidate c; c.id = newCandidateId(); c.name = "untitled"; c.meta.created_utc = utcNow(); c.meta.tool_version = TOOL_VERSION; loaded.reset(); loadedFile = juce::File(); current = c; applyToLive(c.params); metaToUi(c); baseline = ""; refreshStatus(); }
    void metaToUi(const Candidate& c) { nameEd.setText(c.name, juce::dontSendNotification); authorEd.setText(c.meta.author, juce::dontSendNotification); descEd.setText(c.meta.description, juce::dontSendNotification); notesEd.setText(c.meta.audition_notes, juce::dontSendNotification); clampObsEd.setText(c.meta.clamp_observations, juce::dontSendNotification); engEd.setText(c.meta.engineering_note, juce::dontSendNotification); sourcesEd.setText(c.meta.source_material.joinIntoString("\n"), juce::dontSendNotification); categoryBox.setSelectedId(juce::jmax(1, categories().indexOf(c.category) + 1), juce::dontSendNotification); statusBox.setSelectedId(juce::jmax(1, acceptanceStatuses().indexOf(c.meta.acceptance_status) + 1), juce::dontSendNotification); }
    void refreshStatus() {
        if (listeningToB) { /* edits while listening to B belong to B */ }
        Candidate c = uiToCandidate(); const bool init = isInit(c.params);
        juce::String st;
        if (loaded) { const bool mod = serializeCandidate(c) != baseline; st = (mod ? "MODIFIED  " : "SAVED  ") + loaded->name + "  r" + juce::String(loaded->revision) + "  (" + loadedFile.getFileName() + ")"; saveRevBtn.setEnabled(mod); overwriteBtn.setEnabled(mod); }
        else { st = init ? "INIT (unsaved, the six defaults)" : "CUSTOM (unsaved)"; saveRevBtn.setEnabled(true); overwriteBtn.setEnabled(false); }
        candStatus.setText("Status: " + st, juce::dontSendNotification);
        idLbl.setText("id " + c.id + "   revision " + juce::String(c.revision) + "   created " + c.meta.created_utc, juce::dontSendNotification);
        auto fmt = [](const ProductParameters& p) { return juce::String(p.sp_input_level_db, 2) + " / " + juce::String(p.sp_input_gain_db) + " / " + juce::String(p.interstage_level_db, 2) + " / " + juce::String(mpc_gain_name(p.mpc_input_gain)) + " / " + juce::String(p.output_trim_db, 2) + (p.plugin_bypass ? " / BYP" : ""); };
        abStatus.setText(juce::String("Listening to ") + (listeningToB ? "B" : "A") + ".   A = " + fmt(listeningToB ? aParams : c.params) + "   B = " + fmt(listeningToB ? c.params : bParams) + "   (values: SP level / SP gain / interstage / MPC gain / trim; no automatic loudness matching)", juce::dontSendNotification);
        aBtn.setToggleState(!listeningToB, juce::dontSendNotification); bBtn.setToggleState(listeningToB, juce::dontSendNotification);
    }
    void refreshSourceInfo() {
        const int row = sourceList.getSelectedRow(); if (row < 0 || row >= static_cast<int>(sources.size())) { sourceInfo.setText("no source selected", juce::dontSendNotification); return; }
        const Source& s = sources[static_cast<std::size_t>(row)];
        sourceInfo.setText(s.file.getFileName() + "  " + juce::String(s.rate) + " Hz  " + juce::String(s.audio.getNumSamples() / static_cast<double>(s.rate), 2) + " s   sample peak L/R " + dbs(s.analysis.peak[0]) + " / " + dbs(s.analysis.peak[1]) + "   RMS " + dbs(s.analysis.rms[0]) + " / " + dbs(s.analysis.rms[1]) + "  (file analysis)   sha256 " + s.sha256.substring(0, 12), juce::dontSendNotification);
    }
    void play() {
        const int row = sourceList.getSelectedRow(); if (row < 0 || row >= static_cast<int>(sources.size())) return;
        live.transport.stop(); live.transport.setSource(nullptr); reader.reset();
        std::unique_ptr<juce::AudioFormatReader> r(formats.createReaderFor(sources[static_cast<std::size_t>(row)].file)); if (!r) return;
        const double srcRate = r->sampleRate; reader = std::make_unique<juce::AudioFormatReaderSource>(r.release(), true); reader->setLooping(loopToggle.getToggleState());
        live.transport.setSource(reader.get(), 0, nullptr, srcRate);   // transport resamples to the device rate for PLAYBACK only (audition convenience; offline renders use the file's own rate)
        live.transport.setPosition(0.0); live.transport.start();
    }
    void chooseSource() { chooser = std::make_unique<juce::FileChooser>("Load a stereo WAV/AIFF reference beat", juce::File(), "*.wav;*.aif;*.aiff"); chooser->launchAsync(juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectFiles | juce::FileBrowserComponent::canSelectMultipleItems, [this](const juce::FileChooser& fc) { for (auto& f : fc.getResults()) { juce::String err; if (!addSource(f, err)) juce::AlertWindow::showMessageBoxAsync(juce::MessageBoxIconType::WarningIcon, "Source", f.getFileName() + ": " + err); } }); }
    void removeSource() { const int row = sourceList.getSelectedRow(); if (row < 0 || row >= static_cast<int>(sources.size())) return; live.transport.stop(); live.transport.setSource(nullptr); reader.reset(); sources.erase(sources.begin() + row); sourceList.updateContent(); refreshSourceInfo(); }
    void chooseCandidate() { chooser = std::make_unique<juce::FileChooser>("Open a candidate preset", candidatesDir(), "*.json"); chooser->launchAsync(juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectFiles, [this](const juce::FileChooser& fc) { auto f = fc.getResult(); if (f == juce::File()) return; juce::String err; if (!loadCandidate(f, err)) juce::AlertWindow::showMessageBoxAsync(juce::MessageBoxIconType::WarningIcon, "Candidate rejected", err + "\nNothing was applied."); }); }
    void save(bool overwrite) {
        Candidate c = uiToCandidate(); if (c.name.isEmpty()) { juce::AlertWindow::showMessageBoxAsync(juce::MessageBoxIconType::WarningIcon, "Save", "Give the candidate a name first."); return; }
        if (loaded && !overwrite) c.revision = loaded->revision + 1;                       // a modified candidate becomes a NEW revision; the original file is untouched
        c.meta.modified_utc = utcNow(); c.meta.tool_version = TOOL_VERSION; if (c.meta.created_utc.isEmpty()) c.meta.created_utc = c.meta.modified_utc;
        candidatesDir().createDirectory();
        const juce::File f = (overwrite && loaded) ? loadedFile : candidatesDir().getChildFile(c.id + "_r" + juce::String(c.revision) + ".json");
        if (!overwrite && f.existsAsFile()) { juce::AlertWindow::showMessageBoxAsync(juce::MessageBoxIconType::WarningIcon, "Save", f.getFileName() + " already exists; use Overwrite explicitly or change the revision."); return; }
        if (!saveCandidateFile(f, c)) { juce::AlertWindow::showMessageBoxAsync(juce::MessageBoxIconType::WarningIcon, "Save", "could not write " + f.getFullPathName()); return; }
        loaded = c; loadedFile = f; current = c; baseline = serializeCandidate(uiToCandidate()); refreshStatus();
    }
    void exportManifest() {
        juce::Array<juce::var> list; juce::Array<juce::File> files = candidatesDir().findChildFiles(juce::File::findFiles, true, "*.json");
        files.sort();
        for (auto& f : files) { if (f.getFileName() == "MANIFEST.json") continue; Candidate c; auto r = loadCandidateFile(f, c); auto* o = new juce::DynamicObject(); o->setProperty("file", f.getRelativePathFrom(candidatesDir())); o->setProperty("valid", r.ok); if (r.ok) { o->setProperty("id", c.id); o->setProperty("name", c.name); o->setProperty("category", c.category); o->setProperty("revision", c.revision); o->setProperty("acceptance_status", c.meta.acceptance_status); } else o->setProperty("reject_code", r.code); juce::MemoryBlock mb; f.loadFileAsData(mb); o->setProperty("sha256", LabEngine::sha256(mb.getData(), mb.getSize())); list.add(juce::var(o)); }
        auto* root = new juce::DynamicObject(); root->setProperty("record", "smlsp3000-preset-candidate-manifest"); root->setProperty("schema", 1); root->setProperty("generated_utc", utcNow()); root->setProperty("tool_version", TOOL_VERSION); root->setProperty("note", "development candidate manifest; NOT a factory bank; nothing here is part of the plugin state"); root->setProperty("candidates", list);
        const juce::File out = candidatesDir().getChildFile("MANIFEST.json"); out.replaceWithText(juce::JSON::toString(juce::var(root), false) + "\n");
        reportEd.setText("Manifest written: " + out.getFullPathName() + " (" + juce::String(list.size()) + " files)");
    }
    void compareAB() {
        if (sources.empty()) { reportEd.setText("Load a source first."); return; }
        const Source& src = sources[static_cast<std::size_t>(juce::jlimit(0, static_cast<int>(sources.size()) - 1, sourceList.getSelectedRow()))];
        const ProductParameters a = listeningToB ? aParams : currentParams(), b = listeningToB ? currentParams() : bParams;
        juce::AudioBuffer<double> oa, ob; auto ra = renderEngine.render(src.audio, src.rate, a, oa); auto rb = renderEngine.render(src.audio, src.rate, b, ob);
        auto col = [](const juce::String& s) { return s.paddedRight(' ', 34); };
        auto fp = [](const ProductParameters& p, int i) { switch (i) { case 0: return juce::String(p.sp_input_level_db, 2) + " dB"; case 1: return juce::String(p.sp_input_gain_db) + " dB"; case 2: return juce::String(p.interstage_level_db, 2) + " dB"; case 3: return juce::String(mpc_gain_name(p.mpc_input_gain)); case 4: return juce::String(p.output_trim_db, 2) + " dB"; default: return juce::String(p.plugin_bypass ? "on" : "off"); } };
        const char* names[6] = {"SP input level", "SP input gain", "Interstage level", "MPC input gain", "Output trim", "Bypass"};
        juce::String t = "COMPARE on " + src.file.getFileName() + " @ " + juce::String(src.rate) + " Hz\n" + col("") + col("A") + "B\n";
        for (int i = 0; i < 6; ++i) t << col(names[i]) << col(fp(a, i)) << fp(b, i) << "\n";
        if (ra.ok && rb.ok) {
            t << col("SP 12-bit clamps L/R") << col(juce::String(ra.clamps.sp_clip[0]) + " / " + juce::String(ra.clamps.sp_clip[1])) << juce::String(rb.clamps.sp_clip[0]) + " / " + juce::String(rb.clamps.sp_clip[1]) << "\n";
            t << col("MPC 18-bit clamps L/R") << col(juce::String(ra.clamps.mpc_clip18[0]) + " / " + juce::String(ra.clamps.mpc_clip18[1])) << juce::String(rb.clamps.mpc_clip18[0]) + " / " + juce::String(rb.clamps.mpc_clip18[1]) << "\n";
            t << col("16-bit storage clamps L/R") << col(juce::String(ra.clamps.mpc_clamp16[0]) + " / " + juce::String(ra.clamps.mpc_clamp16[1])) << juce::String(rb.clamps.mpc_clamp16[0]) + " / " + juce::String(rb.clamps.mpc_clamp16[1]) << "\n";
            t << col("Output over-range") << col((ra.clamps.output_over_range[0] || ra.clamps.output_over_range[1]) ? "YES" : "NO") << ((rb.clamps.output_over_range[0] || rb.clamps.output_over_range[1]) ? "YES" : "NO") << "\n";
            t << col("Output sample peak L") << col(dbs(ra.output.peak[0])) << dbs(rb.output.peak[0]) << "\n" << col("Output RMS L (file analysis)") << col(dbs(ra.output.rms[0])) << dbs(rb.output.rms[0]) << "\n";
            t << "Level difference B-A (RMS L): " << juce::String(20.0 * std::log10(juce::jmax(1e-12, rb.output.rms[0]) / juce::jmax(1e-12, ra.output.rms[0])), 2) << " dB - audition-only information for MANUAL level matching; nothing is normalised and no preset value is changed.\n";
        } else t << "render failed: " << (ra.ok ? rb.error : ra.error) << "\n";
        reportEd.setText(t);
    }
    void openAudioSettings() { auto* sel = new juce::AudioDeviceSelectorComponent(devices, 0, 0, 2, 2, false, false, true, false); sel->setSize(520, 420); juce::DialogWindow::LaunchOptions o; o.content.setOwned(sel); o.dialogTitle = "Audio settings (Preset Lab playback only)"; o.componentToCentreAround = this; o.resizable = false; o.launchAsync(); }
    void openManual() { const juce::File m = repoRoot().getChildFile("docs").getChildFile("SML_SP3000_MANUAL.md"); if (m.existsAsFile()) m.startAsProcess(); else juce::AlertWindow::showMessageBoxAsync(juce::MessageBoxIconType::InfoIcon, "Manual", "docs/SML_SP3000_MANUAL.md was not found next to this build (" + m.getFullPathName() + ")."); }
    // ListBoxModel
    int getNumRows() override { return static_cast<int>(sources.size()); }
    void paintListBoxItem(int row, juce::Graphics& g, int w, int h, bool sel) override { if (sel) g.fillAll(juce::Colour(0xff3a4150)); g.setColour(juce::Colours::white); g.setFont(12.0f); if (row < static_cast<int>(sources.size())) g.drawText(sources[static_cast<std::size_t>(row)].file.getFileName() + "  (" + juce::String(sources[static_cast<std::size_t>(row)].rate) + " Hz)", 6, 0, w - 8, h, juce::Justification::centredLeft); }
    void selectedRowsChanged(int) override { refreshSourceInfo(); }
    void timerCallback() override {
        const auto s = liveProc.adapter().meters(); const bool avail = s.prepared && liveProc.rateSupported();
        inL.setValues(s.input_peak[0], s.input_peak_hold[0], avail); inR.setValues(s.input_peak[1], s.input_peak_hold[1], avail);
        mpcL.setValues(s.mpc_core_input_peak[0], s.mpc_core_input_peak[0], avail); mpcR.setValues(s.mpc_core_input_peak[1], s.mpc_core_input_peak[1], avail);
        outL.setValues(s.output_peak[0], s.output_peak_hold[0], avail, s.output_over_range[0]); outR.setValues(s.output_peak[1], s.output_peak_hold[1], avail, s.output_over_range[1]);
        countersLbl.setText(avail ? "SP 12-bit clamps L " + juce::String(s.sp_clip[0]) + " R " + juce::String(s.sp_clip[1]) + "   |   MPC 18-bit clamps L " + juce::String(s.mpc_clip18[0]) + " R " + juce::String(s.mpc_clip18[1]) + "   |   16-bit storage clamps L " + juce::String(s.mpc_clamp16[0]) + " R " + juce::String(s.mpc_clamp16[1]) + "   |   over-range " + juce::String((s.output_over_range[0] || s.output_over_range[1]) ? "YES" : "NO") + "   |   non-finite in " + juce::String(s.nonfinite_input_samples) + "   faults " + juce::String(s.faults) + (s.fault_latched ? " (LATCHED)" : "") : "telemetry unavailable (live processor not prepared: no audio device or playback not started)", juce::dontSendNotification);
        rateLbl.setText(avail ? "host rate " + juce::String(s.host_rate) + " Hz   latency " + juce::String(s.latency) + " samples (" + juce::String(1000.0 * s.latency / s.host_rate, 2) + " ms)   bypass weight " + juce::String(s.bypass_weight, 2) + "   prepared " + (s.prepared ? "yes" : "no") + "   blocks " + juce::String(s.blocks_processed) + (live.transport.isPlaying() ? "   PLAYING " + juce::String(live.transport.getCurrentPosition(), 1) + " s" : (telemetryNote.isNotEmpty() ? "   " + telemetryNote : "   stopped")) : "host rate -   latency -   (unavailable)", juce::dontSendNotification);
    }
    void paint(juce::Graphics& g) override { g.fillAll(juce::Colour(0xff23272e)); auto box = [&](juce::Rectangle<int> r) { g.setColour(juce::Colour(0xff2d323b)); g.fillRoundedRectangle(r.toFloat(), 6.0f); g.setColour(juce::Colour(0xff454c58)); g.drawRoundedRectangle(r.toFloat(), 6.0f, 1.0f); }; for (auto& r : panels) box(r); }
    void resized() override {
        auto a = getLocalBounds().reduced(12); title.setBounds(a.removeFromTop(24)); claim.setBounds(a.removeFromTop(16)); a.removeFromTop(4);
        auto top = a.removeFromTop(static_cast<int>(a.getHeight() * 0.62)); auto bottom = a.withTrimmedTop(6);
        auto src = top.removeFromLeft(top.getWidth() * 30 / 100).reduced(3), meta = top.removeFromRight(top.getWidth() * 42 / 100).reduced(3), cand = top.reduced(3);
        panels = {src, cand, meta, bottom};
        // sources
        auto s = src.reduced(8); secSource.setBounds(s.removeFromTop(20)); auto row = s.removeFromTop(24); loadSourceBtn.setBounds(row.removeFromLeft(90)); removeSourceBtn.setBounds(row.removeFromLeft(80).withTrimmedLeft(4)); audioSettingsBtn.setBounds(row.withTrimmedLeft(4));
        sourceList.setBounds(s.removeFromTop(juce::jmax(60, s.getHeight() - 150))); s.removeFromTop(4); row = s.removeFromTop(24); playBtn.setBounds(row.removeFromLeft(60)); stopBtn.setBounds(row.removeFromLeft(60).withTrimmedLeft(4)); loopToggle.setBounds(row.withTrimmedLeft(6));
        sourceInfo.setBounds(s.removeFromTop(36)); deviceInfo.setBounds(s.removeFromTop(18)); monitorLbl.setBounds(s.removeFromTop(16)); monitorTrim.setBounds(s.removeFromTop(22)); row = s.removeFromTop(24); helpBtn.setBounds(row.removeFromLeft(110)); aboutBtn.setBounds(row.removeFromLeft(70).withTrimmedLeft(4));
        // candidate controls
        auto c = cand.reduced(8); secCandidate.setBounds(c.removeFromTop(20)); candStatus.setBounds(c.removeFromTop(20)); auto knobs = c.removeFromTop(juce::jmax(120, c.getHeight() / 2)); const int kw = knobs.getWidth() / 3;
        auto rot = [&](juce::Rectangle<int> r, juce::Label& l, juce::Slider& sl) { l.setBounds(r.removeFromTop(18)); sl.setBounds(r.reduced(4)); };
        rot(knobs.removeFromLeft(kw), spLevelLbl, spLevel); rot(knobs.removeFromLeft(kw), interLbl, interstage); rot(knobs, trimLbl, trim);
        auto sw = c.removeFromTop(48); const int sw2 = sw.getWidth() / 2; auto cb = [&](juce::Rectangle<int> r, juce::Label& l, juce::ComboBox& b) { l.setBounds(r.removeFromTop(18)); b.setBounds(r.removeFromTop(24).reduced(8, 0)); }; cb(sw.removeFromLeft(sw2), spGainLbl, spGain); cb(sw, mpcGainLbl, mpcGain);
        row = c.removeFromTop(26); bypassToggle.setBounds(row.removeFromLeft(row.getWidth() / 2)); resetBtn.setBounds(row.removeFromLeft(110)); bypassCmpBtn.setBounds(row.withTrimmedLeft(4));
        c.removeFromTop(4); row = c.removeFromTop(24); aBtn.setBounds(row.removeFromLeft(50)); bBtn.setBounds(row.removeFromLeft(50).withTrimmedLeft(4)); bInitBtn.setBounds(row.removeFromLeft(80).withTrimmedLeft(4)); copyABBtn.setBounds(row.removeFromLeft(90).withTrimmedLeft(4)); compareBtn.setBounds(row.removeFromLeft(110).withTrimmedLeft(4)); renderBtn.setBounds(row.withTrimmedLeft(4));
        abStatus.setBounds(c.removeFromTop(34));
        // metadata
        auto m = meta.reduced(8); secMeta.setBounds(m.removeFromTop(20)); row = m.removeFromTop(24); newBtn.setBounds(row.removeFromLeft(50)); openBtn.setBounds(row.removeFromLeft(60).withTrimmedLeft(4)); saveRevBtn.setBounds(row.removeFromLeft(130).withTrimmedLeft(4)); overwriteBtn.setBounds(row.removeFromLeft(90).withTrimmedLeft(4)); exportManifestBtn.setBounds(row.withTrimmedLeft(4));
        idLbl.setBounds(m.removeFromTop(16)); auto two = m.removeFromTop(40); auto l2 = two.removeFromLeft(two.getWidth() / 2); nameLbl.setBounds(l2.removeFromTop(16)); nameEd.setBounds(l2.reduced(2, 0)); authorLbl.setBounds(two.removeFromTop(16)); authorEd.setBounds(two.reduced(2, 0));
        two = m.removeFromTop(40); l2 = two.removeFromLeft(two.getWidth() / 2); categoryLbl.setBounds(l2.removeFromTop(16)); categoryBox.setBounds(l2.reduced(2, 0)); statusLbl.setBounds(two.removeFromTop(16)); statusBox.setBounds(two.reduced(2, 0));
        const int eh = juce::jmax(34, (m.getHeight() - 5 * 16) / 5);
        auto ed = [&](juce::Label& l, juce::TextEditor& e) { l.setBounds(m.removeFromTop(16)); e.setBounds(m.removeFromTop(eh).reduced(2, 1)); };
        ed(descLbl, descEd); ed(notesLbl, notesEd); ed(clampObsLbl, clampObsEd); ed(sourcesLbl, sourcesEd); ed(engLbl, engEd);
        // telemetry
        auto t = bottom.reduced(8); secTelemetry.setBounds(t.removeFromTop(20)); auto meters = t.removeFromLeft(t.getWidth() / 2); auto rep = t.withTrimmedLeft(8);
        auto mrow = [&](juce::Label& l, PeakMeter& x, PeakMeter& y) { l.setBounds(meters.removeFromTop(16)); auto r = meters.removeFromTop(18); x.setBounds(r.removeFromLeft(r.getWidth() / 2).reduced(2, 1)); y.setBounds(r.reduced(2, 1)); };
        mrow(inLbl, inL, inR); mrow(mpcLbl, mpcL, mpcR); mrow(outLbl, outL, outR); countersLbl.setBounds(meters.removeFromTop(18)); rateLbl.setBounds(meters.removeFromTop(18));
        reportEd.setBounds(rep);
    }
    struct ParamWatch : juce::AudioProcessorParameter::Listener { std::function<void()> onChange; void parameterValueChanged(int, float) override { juce::MessageManager::callAsync([this] { if (onChange) onChange(); }); } void parameterGestureChanged(int, bool) override {} } paramWatch;

    juce::String telemetryNote;
    juce::AudioFormatManager formats; SMLProcessor liveProc; LiveSource live; LabEngine renderEngine; juce::AudioDeviceManager devices; juce::AudioSourcePlayer player; std::unique_ptr<juce::AudioFormatReaderSource> reader; std::unique_ptr<juce::FileChooser> chooser;
    std::vector<Source> sources; Candidate current; std::optional<Candidate> loaded; juce::File loadedFile; juce::String baseline, lastReport;
    ProductParameters aParams = ProductParameters::defaults(), bParams = ProductParameters::defaults(); bool listeningToB = false;
    juce::Label title, claim, secSource, secCandidate, secMeta, secTelemetry, sourceInfo, deviceInfo, monitorLbl, abStatus, candStatus, idLbl, spLevelLbl, interLbl, trimLbl, spGainLbl, mpcGainLbl, nameLbl, authorLbl, descLbl, notesLbl, clampObsLbl, engLbl, sourcesLbl, categoryLbl, statusLbl, inLbl, mpcLbl, outLbl, countersLbl, rateLbl;
    juce::ListBox sourceList; juce::TextButton loadSourceBtn{"Load..."}, removeSourceBtn{"Remove"}, playBtn{"Play"}, stopBtn{"Stop"}, audioSettingsBtn{"Audio settings..."}, renderBtn{"Render audition..."}, compareBtn{"Compare A/B"}, newBtn{"New"}, openBtn{"Open..."}, saveRevBtn{"Save (new revision)"}, overwriteBtn{"Overwrite"}, exportManifestBtn{"Export manifest"}, resetBtn{"Reset to INIT"}, aBtn{"A"}, bBtn{"B"}, bInitBtn{"B = INIT"}, copyABBtn{"Copy A -> B"}, bypassCmpBtn{"Processed / Bypass"}, helpBtn{"Help (manual)"}, aboutBtn{"About"};
    juce::ToggleButton loopToggle{"Loop"}, bypassToggle{"Bypass (latency-aligned dry, 10 ms crossfade)"};
    juce::Slider spLevel, interstage, trim, monitorTrim; juce::ComboBox spGain, mpcGain, categoryBox, statusBox;
    std::unique_ptr<juce::SliderParameterAttachment> spLevelAtt, interAtt, trimAtt; std::unique_ptr<juce::ComboBoxParameterAttachment> spGainAtt, mpcGainAtt; std::unique_ptr<juce::ButtonParameterAttachment> bypassAtt;
    juce::TextEditor nameEd, authorEd, descEd, notesEd, clampObsEd, engEd, sourcesEd, reportEd;
    PeakMeter inL, inR, mpcL, mpcR, outL, outR; std::vector<juce::Rectangle<int>> panels;
};

// ---------------------------------------------------------------- headless helpers
static void printJson(const juce::var& v) { std::printf("%s\n", juce::JSON::toString(v, true).toRawUTF8()); }
static juce::var resultVar(const ParseResult& r) { auto* o = new juce::DynamicObject(); o->setProperty("ok", r.ok); o->setProperty("code", r.code); o->setProperty("detail", r.detail); return juce::var(o); }

static int headless(const juce::StringArray& args, bool& handled) {
    handled = true;
    if (args.contains("--validate")) { Candidate c; auto r = loadCandidateFile(juce::File::getCurrentWorkingDirectory().getChildFile(args[args.indexOf("--validate") + 1]), c); printJson(resultVar(r)); return r.ok ? 0 : 1; }
    if (args.contains("--roundtrip")) { const int i = args.indexOf("--roundtrip"); Candidate c; auto r = loadCandidateFile(juce::File::getCurrentWorkingDirectory().getChildFile(args[i + 1]), c); if (!r.ok) { printJson(resultVar(r)); return 1; } const bool ok = saveCandidateFile(juce::File::getCurrentWorkingDirectory().getChildFile(args[i + 2]), c); auto* o = new juce::DynamicObject(); o->setProperty("ok", ok); o->setProperty("state_text", nativeStateText(c.params)); printJson(juce::var(o)); return ok ? 0 : 1; }
    if (args.contains("--init-state")) { std::printf("%s", nativeStateText(ProductParameters::defaults()).toRawUTF8()); return 0; }
    if (args.contains("--render")) {
        const int i = args.indexOf("--render"); if (args.size() < i + 4) { std::printf("{\"ok\":false,\"error\":\"usage: --render <candidate.json|INIT> <source.wav> <out_dir> [--block N]\"}\n"); return 2; }
        Candidate c; if (args[i + 1] == "INIT") { c.id = "INIT"; c.name = "INIT"; } else { auto r = loadCandidateFile(juce::File::getCurrentWorkingDirectory().getChildFile(args[i + 1]), c); if (!r.ok) { printJson(resultVar(r)); return 1; } }
        juce::AudioBuffer<double> src; int rate = 0; juce::String err; const juce::File sf = juce::File::getCurrentWorkingDirectory().getChildFile(args[i + 2]);
        if (!LabEngine::readAudioFile(sf, src, rate, err)) { std::printf("{\"ok\":false,\"error\":\"%s\"}\n", err.toRawUTF8()); return 1; }
        const int block = args.contains("--block") ? args[args.indexOf("--block") + 1].getIntValue() : 512;
        LabEngine lab; juce::AudioBuffer<double> out; auto rec = lab.render(src, rate, c.params, out, block); rec.candidate_id = c.id; rec.candidate_revision = c.revision;
        if (!rec.ok) { std::printf("{\"ok\":false,\"error\":\"%s\"}\n", rec.error.toRawUTF8()); return 1; }
        const juce::File dir = juce::File::getCurrentWorkingDirectory().getChildFile(args[i + 3]); dir.createDirectory();
        const juce::String base = c.id + "_r" + juce::String(c.revision) + "_" + sf.getFileNameWithoutExtension() + "_" + juce::String(rate); const juce::File wav = dir.getChildFile(base + ".wav"), js = dir.getChildFile(base + ".render.json"), raw = dir.getChildFile(base + ".f64");
        if (!LabEngine::writeWav32f(wav, out, rate)) { std::printf("{\"ok\":false,\"error\":\"cannot write wav\"}\n"); return 1; }
        { std::vector<double> inter(static_cast<std::size_t>(out.getNumSamples()) * 2); for (int k = 0; k < out.getNumSamples(); ++k) { inter[2 * static_cast<std::size_t>(k)] = out.getSample(0, k); inter[2 * static_cast<std::size_t>(k) + 1] = out.getSample(1, k); } raw.deleteFile(); juce::FileOutputStream os(raw); os.write(inter.data(), inter.size() * sizeof(double)); }
        { juce::MemoryBlock mb; wav.loadFileAsData(mb); rec.output_file_sha256 = LabEngine::sha256(mb.getData(), mb.getSize()); }
        const juce::var v = rec.toVar(SMLSP3000_LAB_BUILD_ID, sf.getFullPathName(), wav.getFullPathName()); js.replaceWithText(juce::JSON::toString(v, false) + "\n"); v.getDynamicObject()->setProperty("raw_f64_path", raw.getFullPathName()); printJson(v); return 0;
    }
    handled = false; return 0;
}

// ---------------------------------------------------------------- application
class LabWindow : public juce::DocumentWindow {
public:
    LabWindow() : DocumentWindow("SML SP-3000 Preset Lab", juce::Colour(0xff23272e), allButtons) { setUsingNativeTitleBar(true); comp = new LabComponent(); setContentOwned(comp, true); setResizable(true, false); setResizeLimits(1100, 700, 2400, 1600); centreWithSize(getWidth(), getHeight()); setVisible(true); }
    void closeButtonPressed() override { juce::JUCEApplication::getInstance()->systemRequestedQuit(); }
    LabComponent* comp = nullptr;
};

class LabApp : public juce::JUCEApplication {
public:
    const juce::String getApplicationName() override { return "SML SP-3000 Preset Lab"; }
    const juce::String getApplicationVersion() override { return TOOL_VERSION; }
    bool moreThanOneInstanceAllowed() override { return true; }
    void initialise(const juce::String& cmd) override {
        juce::StringArray args = juce::StringArray::fromTokens(cmd, true); for (auto& a : args) a = a.unquoted();
        bool handled = false; const int rc = headless(args, handled);
        if (handled) { setApplicationReturnValue(rc); quit(); return; }
        window = std::make_unique<LabWindow>();
        if (args.contains("--snapshot")) { setApplicationReturnValue(snapshot(args)); quit(); return; }
        if (args.size() > 0 && args[0].endsWith(".json")) { juce::String err; if (!window->comp->loadCandidate(juce::File::getCurrentWorkingDirectory().getChildFile(args[0]), err)) std::printf("candidate rejected: %s\n", err.toRawUTF8()); }
    }
    int snapshot(const juce::StringArray& args) {
        const int i = args.indexOf("--snapshot"); if (args.size() < i + 3) { std::printf("usage: --snapshot <out_dir> <source.wav> [candidate.json ...]\n"); return 2; }
        const juce::File dir = juce::File::getCurrentWorkingDirectory().getChildFile(args[i + 1]); dir.createDirectory(); auto* c = window->comp; int rc = 0;
        juce::String err; if (!c->addSource(juce::File::getCurrentWorkingDirectory().getChildFile(args[i + 2]), err)) { std::printf("source: %s\n", err.toRawUTF8()); return 1; }
        auto pump = [](int ms) { juce::MessageManager::getInstance()->runDispatchLoopUntil(ms); };
        auto save = [&](const juce::String& name) { pump(150); juce::Image img = c->createComponentSnapshot(c->getLocalBounds(), true, 1.0f); juce::PNGImageFormat png; const juce::File f = dir.getChildFile(name + ".png"); f.deleteFile(); juce::FileOutputStream os(f); if (!os.openedOk() || !png.writeImageToStream(img, os)) { std::printf("failed %s\n", f.getFullPathName().toRawUTF8()); rc = 1; } else std::printf("wrote %s (%dx%d)\n", f.getFullPathName().toRawUTF8(), img.getWidth(), img.getHeight()); };
        pump(200); c->renderCurrent(); save("preset_lab_01_init");
        int k = 2; for (int j = i + 3; j < args.size(); ++j, ++k) { if (!c->loadCandidate(juce::File::getCurrentWorkingDirectory().getChildFile(args[j]), err)) { std::printf("candidate %s: %s\n", args[j].toRawUTF8(), err.toRawUTF8()); rc = 1; continue; } c->renderCurrent(); save("preset_lab_" + juce::String(k).paddedLeft('0', 2) + "_" + juce::File(args[j]).getFileNameWithoutExtension()); }
        c->setModifiedForDemo(); save("preset_lab_" + juce::String(k).paddedLeft('0', 2) + "_metadata_modified_save_view");
        return rc;
    }
    void shutdown() override { window.reset(); }
    void systemRequestedQuit() override { quit(); }
private:
    std::unique_ptr<LabWindow> window;
};
START_JUCE_APPLICATION(LabApp)
