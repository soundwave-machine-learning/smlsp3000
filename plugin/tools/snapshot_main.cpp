// Development tool: instantiate the processor + editor under a (virtual) display and write PNG snapshots at several sizes.
// Also exercises editor-before-prepare and repeated open/close. Not part of the product.
#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_graphics/juce_graphics.h>
#include "PluginProcessor.h"
#include "PluginEditor.h"

class SnapshotApp : public juce::JUCEApplication {
public:
    const juce::String getApplicationName() override { return "smlsp3000_editor_snapshot"; }
    const juce::String getApplicationVersion() override { return "0.7.0"; }
    void initialise(const juce::String& cmd) override {
        juce::StringArray args = juce::StringArray::fromTokens(cmd, true);
        const juce::File outDir(args.size() > 0 ? args[0].unquoted() : juce::String("."));
        outDir.createDirectory();
        int rc = 0;
        {   // diagnostics: typeface actually resolved for label text, and the text of the first visible labels (encoding check)
            juce::Font f(juce::FontOptions(12.5f)); std::printf("typeface=%s\n", f.getTypefaceName().toRawUTF8());
            if (auto tf = f.getTypefacePtr()) std::printf("typeface_resolved=%s style=%s\n", tf->getName().toRawUTF8(), tf->getStyle().toRawUTF8());
            std::printf("available_fonts=%s\n", juce::Font::findAllTypefaceNames().joinIntoString(", ").toRawUTF8());
        }
        {   // editor before prepare
            SMLProcessor proc; std::unique_ptr<juce::AudioProcessorEditor> ed(proc.createEditor());
            auto* e = dynamic_cast<SMLEditor*>(ed.get()); e->setSize(SMLEditor::kDefW, SMLEditor::kDefH);
            for (auto* c : e->getChildren()) if (auto* l = dynamic_cast<juce::Label*>(c)) if (l->getText().startsWith("SP INPUT")) std::printf("path_label_text=%s\n", l->getText().toRawUTF8());
            juce::MessageManager::getInstance()->runDispatchLoopUntil(80);
            save(*e, outDir.getChildFile("editor_before_prepare_920x540.png"), rc);
            // prepare and feed a block so meters show real values
            proc.prepareToPlay(48000.0, 512); juce::AudioBuffer<float> buf(2, 512); juce::MidiBuffer midi;
            for (int b = 0; b < 40; ++b) { for (int c = 0; c < 2; ++c) for (int i = 0; i < 512; ++i) buf.setSample(c, i, 0.6f * std::sin(2.0f * 3.1415926f * 440.0f * (float)(b * 512 + i) / 48000.0f)); proc.processBlock(buf, midi); }
            juce::MessageManager::getInstance()->runDispatchLoopUntil(120);
            save(*e, outDir.getChildFile("editor_default_920x540.png"), rc);
            e->setSize(SMLEditor::kMinW, SMLEditor::kMinH); juce::MessageManager::getInstance()->runDispatchLoopUntil(80); save(*e, outDir.getChildFile("editor_min_760x440.png"), rc);
            e->setSize(SMLEditor::kMaxW, SMLEditor::kMaxH); juce::MessageManager::getInstance()->runDispatchLoopUntil(80); save(*e, outDir.getChildFile("editor_max_1520x880.png"), rc);
            proc.parameterFor(smlsp3000::ParamId::PLUGIN_BYPASS)->setValueNotifyingHost(1.0f); for (int b = 0; b < 4; ++b) proc.processBlock(buf, midi);
            e->setSize(SMLEditor::kDefW, SMLEditor::kDefH); juce::MessageManager::getInstance()->runDispatchLoopUntil(120); save(*e, outDir.getChildFile("editor_bypassed_920x540.png"), rc);
        }
        for (int k = 0; k < 20; ++k) { SMLProcessor proc; std::unique_ptr<juce::AudioProcessorEditor> ed(proc.createEditor()); ed.reset(); }   // repeated open/close
        std::printf("snapshot tool done rc=%d\n", rc); setApplicationReturnValue(rc); quit();
    }
    void save(juce::Component& c, const juce::File& f, int& rc) {
        juce::Image img = c.createComponentSnapshot(c.getLocalBounds(), true, 1.0f); juce::PNGImageFormat png; f.deleteFile(); juce::FileOutputStream os(f);   // FileOutputStream appends to an existing file: remove any previous capture first
        if (!os.openedOk() || !png.writeImageToStream(img, os)) { std::printf("failed %s\n", f.getFullPathName().toRawUTF8()); rc = 1; } else std::printf("wrote %s (%dx%d)\n", f.getFullPathName().toRawUTF8(), img.getWidth(), img.getHeight());
    }
    void shutdown() override {}
};
START_JUCE_APPLICATION(SnapshotApp)
