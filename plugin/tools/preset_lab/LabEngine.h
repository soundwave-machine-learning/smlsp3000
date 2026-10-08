// SML SP-3000 Preset Lab - audition/render engine. It owns ONE product processor (SMLProcessor -> HostAdapter -> native core):
// the exact plugin processing path; the lab adds no DSP. Candidate values are applied through the plugin's own host
// parameters (the same normalised mapping a DAW or a session restore uses), so a lab render is what the plugin renders.
#pragma once
#include <juce_audio_basics/juce_audio_basics.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include "PluginProcessor.h"
#include "PresetCandidate.h"

namespace preset_lab {

struct EffectiveValues { double v[6]{}; };   // the values the adapter actually holds after the host-parameter mapping (float32 normalised)

struct ClampReport {
    std::int64_t sp_clip[2]{}, mpc_clip18[2]{}, mpc_clamp16[2]{};
    bool output_over_range[2]{}; std::int64_t nonfinite_input = 0, faults = 0;
    juce::String text() const;              // the short authoring report (counts only; no good/bad classification)
};

struct FileAnalysis { double peak[2]{}, rms[2]{}; std::int64_t frames = 0; int channels = 0; };   // offline analysis of a buffer (NOT a plugin meter)
FileAnalysis analyse(const juce::AudioBuffer<double>& b);

struct RenderRecord {
    bool ok = false; juce::String error;
    int rate = 0; std::int64_t frames_in = 0, frames_out = 0, latency = 0; int block = 0;
    smlsp3000::ProductParameters stored;   // candidate (physical) values
    EffectiveValues effective;             // values after the plugin's parameter mapping
    ClampReport clamps; FileAnalysis source, output;
    juce::String source_sha256, output_f64_sha256, output_file_sha256, candidate_id; int candidate_revision = 0;
    juce::var toVar(const juce::String& toolBuildId, const juce::String& sourcePath, const juce::String& outputPath) const;
};

class LabEngine {
public:
    LabEngine();
    // Offline, deterministic: prepare at `rate`, apply the candidate through host parameters, re-prepare (stream start, no ramps),
    // process the whole source in blocks of `block`, drain the latency tail. Output is float64 planar.
    RenderRecord render(const juce::AudioBuffer<double>& source, int rate, const smlsp3000::ProductParameters& p, juce::AudioBuffer<double>& out, int block = 512);
    static void applyThroughHostParameters(SMLProcessor& proc, const smlsp3000::ProductParameters& p);   // JUCE parameter path (float normalised)
    static EffectiveValues effectiveValues(const SMLProcessor& proc);
    static smlsp3000::ProductParameters readBackFromAdapter(const SMLProcessor& proc);
    static ClampReport clampReportFrom(const smlsp3000::MeterSnapshot& m);
    static juce::String sha256(const void* data, std::size_t bytes);
    static juce::String sha256(const juce::AudioBuffer<double>& b);
    static bool writeWav32f(const juce::File& f, const juce::AudioBuffer<double>& b, int rate);
    static bool readAudioFile(const juce::File& f, juce::AudioBuffer<double>& out, int& rate, juce::String& err);
    static const juce::StringArray& supportedRates();
    SMLProcessor& processor() { return proc_; }
private:
    SMLProcessor proc_; juce::AudioFormatManager formats_;
};

}  // namespace preset_lab
