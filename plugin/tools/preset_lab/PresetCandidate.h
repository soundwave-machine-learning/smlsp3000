// SML SP-3000 Preset Lab - candidate preset format (development/authoring only; NOT the plugin state, NOT a factory bank).
// A candidate stores the six product controls as PHYSICAL values (dB, step dB, enum name, bool) plus authoring metadata.
// Value validation is delegated to the native core's own state parser (Engine::parse_state) through the schema-v1 state
// text, so a candidate accepts exactly what the plugin would accept; nothing is applied on rejection (no partial application).
#pragma once
#include <juce_core/juce_core.h>
#include "smlsp3000/engine.hpp"

namespace preset_lab {

inline constexpr const char* CANDIDATE_FORMAT = "smlsp3000-preset-candidate";
inline constexpr int CANDIDATE_SCHEMA = 1;
inline constexpr const char* TOOL_VERSION = "smlsp3000-preset-lab-0.1.0";
inline constexpr int CANDIDATE_MAX_BYTES = 256 * 1024;

const juce::StringArray& categories();            // authoring categories only (no category implies hardware authenticity)
const juce::StringArray& acceptanceStatuses();    // DRAFT, AUDITIONED, CANDIDATE, REJECTED, TOOL_DEMO

struct AuthoringMetadata {
    juce::String author, description, audition_notes, clamp_observations, engineering_note;
    juce::StringArray source_material;            // files/descriptions the candidate was auditioned on
    juce::String acceptance_status = "DRAFT";
    double input_peak = -1.0, output_peak = -1.0; // sample peaks (linear) observed on the last audition render; -1 = not recorded
    juce::String created_utc, modified_utc, tool_version, native_core_version, adapter_version;
};

struct Candidate {
    juce::String id, name, category = "EXPERIMENTAL";
    int revision = 1;
    smlsp3000::ProductParameters params = smlsp3000::ProductParameters::defaults();   // INIT = the six frozen defaults
    AuthoringMetadata meta;
};

struct ParseResult { bool ok = false; juce::String code, detail; };

juce::String nativeStateText(const smlsp3000::ProductParameters& p);   // schema-v1 state text (same lines the host adapter writes)
ParseResult validateParameters(const smlsp3000::ProductParameters& p);   // through Engine::parse_state (ranges, enums, finiteness)
bool sameProductParameters(const smlsp3000::ProductParameters& a, const smlsp3000::ProductParameters& b);
bool isInit(const smlsp3000::ProductParameters& p);

ParseResult parseCandidate(const juce::String& jsonText, Candidate& out);   // strict: unknown keys, wrong types, future schema, bad values -> rejected, `out` untouched
juce::String serializeCandidate(const Candidate& c);
ParseResult loadCandidateFile(const juce::File& f, Candidate& out);
bool saveCandidateFile(const juce::File& f, const Candidate& c);
juce::String newCandidateId();
juce::String utcNow();
juce::var candidateToVar(const Candidate& c);

}  // namespace preset_lab
