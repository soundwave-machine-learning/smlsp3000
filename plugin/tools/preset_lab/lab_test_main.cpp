// SML SP-3000 Preset Lab self-test (ctest `preset_lab_test`): candidate format, validation, no partial application,
// INIT equivalence, deterministic renders, metadata independence, same-parameters-same-output. Development only.
#include <juce_gui_basics/juce_gui_basics.h>
#include <cmath>
#include <cstdio>
#include "PresetCandidate.h"
#include "LabEngine.h"

using namespace preset_lab;
using namespace smlsp3000;
static int fails = 0, passes = 0;
#define CHECK(cond, name) do { if (cond) { ++passes; std::printf("PASS %s\n", name); } else { ++fails; std::printf("FAIL %s (line %d)\n", name, __LINE__); } } while (0)

static Candidate demo() { Candidate c; c.id = "cand_test_000000"; c.name = "test"; c.category = "EXPERIMENTAL"; c.params.sp_input_level_db = 6.0; c.params.interstage_level_db = 3.0; c.params.sp_input_gain_db = 20; c.params.mpc_input_gain = MpcInputGain::MID; c.params.output_trim_db = -6.0; c.meta.author = "selftest"; c.meta.description = "d"; c.meta.source_material.add("synthetic"); c.meta.created_utc = "2026-10-08T00:00:00Z"; return c; }

static juce::AudioBuffer<double> synth(int rate, double seconds, double amp) {
    const int n = static_cast<int>(rate * seconds); juce::AudioBuffer<double> b(2, n);
    for (int i = 0; i < n; ++i) { const double t = static_cast<double>(i) / rate; const double env = std::exp(-6.0 * std::fmod(t, 0.25)); const double v = amp * env * (std::sin(2 * M_PI * 55.0 * t) + 0.3 * std::sin(2 * M_PI * 1870.0 * t)); b.setSample(0, i, v); b.setSample(1, i, 0.8 * v); }
    return b;
}

int main() {
    juce::ScopedJuceInitialiser_GUI init;
    // ---- format: round trip
    { Candidate c = demo(); Candidate d; auto r = parseCandidate(serializeCandidate(c), d); CHECK(r.ok, "candidate round trip parses"); CHECK(r.ok && sameProductParameters(c.params, d.params) && d.id == c.id && d.name == c.name && d.category == c.category && d.revision == c.revision && d.meta.author == "selftest" && d.meta.source_material == c.meta.source_material, "candidate round trip preserves values"); 
      CHECK(serializeCandidate(c) == serializeCandidate(d), "candidate serialisation is stable"); }
    // ---- file save/load
    { juce::TemporaryFile tf(".json"); Candidate c = demo(); CHECK(saveCandidateFile(tf.getFile(), c), "candidate file save"); Candidate d; auto r = loadCandidateFile(tf.getFile(), d); CHECK(r.ok && sameProductParameters(c.params, d.params), "candidate file load"); }
    // ---- INIT equivalence
    { Candidate c; CHECK(isInit(c.params), "new candidate is INIT (the six frozen defaults)"); ProductParameters p = ProductParameters::defaults(); CHECK(p.sp_input_level_db == 0.0 && p.sp_input_gain_db == 0 && p.interstage_level_db == 0.0 && p.mpc_input_gain == MpcInputGain::LO && p.output_trim_db == 0.0 && !p.plugin_bypass, "INIT values are 0 dB / 0 dB / 0 dB / LO / 0 dB / off");
      ProductParameters q = ProductParameters::defaults(); q.output_trim_db = -1.0; auto r = Engine::parse_state(nativeStateText(ProductParameters::defaults()).toStdString(), q); CHECK(r.ok && isInit(q), "INIT state text parses back to INIT through the core parser"); }
    // ---- rejections (each leaves `out` untouched)
    auto rejects = [&](const juce::String& json, const char* code, const char* name) { Candidate out = demo(); auto r = parseCandidate(json, out); const bool untouched = sameProductParameters(out.params, demo().params) && out.id == "cand_test_000000"; if (!(!r.ok && r.code == code && untouched)) std::printf("   got code=%s detail=%s\n", r.code.toRawUTF8(), r.detail.toRawUTF8()); CHECK(!r.ok && r.code == code && untouched, name); };
    auto withParam = [&](const char* key, const juce::String& value) { juce::var v = candidateToVar(demo()); v["product_parameters"].getDynamicObject()->setProperty(key, juce::JSON::fromString(value)); return juce::JSON::toString(v); };
    auto withTop = [&](const char* key, const juce::var& value) { juce::var v = candidateToVar(demo()); v.getDynamicObject()->setProperty(key, value); return juce::JSON::toString(v); };
    rejects("{not json", "MALFORMED_JSON", "malformed JSON rejected");
    rejects("[1,2,3]", "MALFORMED_JSON", "non-object rejected");
    rejects(withTop("schema", 2), "UNSUPPORTED_SCHEMA_VERSION", "future schema rejected");
    rejects(withTop("schema", "1"), "MALFORMED_SCHEMA", "non-integer schema rejected");
    rejects(withTop("format", "something-else"), "NOT_A_CANDIDATE", "wrong format tag rejected");
    rejects(withTop("extra", 1), "UNKNOWN_KEY", "unknown top-level key rejected");
    rejects(withTop("category", "FACTORY"), "UNKNOWN_CATEGORY", "unknown category rejected");
    rejects(withTop("revision", 0), "BAD_REVISION", "revision < 1 rejected");
    rejects(withTop("id", "bad id!"), "BAD_ID", "bad id rejected");
    rejects(withParam("sp_input_level_db", "12.5"), "OUT_OF_RANGE", "sp_input_level_db above +12 rejected (core range policy)");
    rejects(withParam("sp_input_level_db", "-60.001"), "OUT_OF_RANGE", "sp_input_level_db below -60 rejected");
    rejects(withParam("interstage_level_db", "24.01"), "OUT_OF_RANGE", "interstage_level_db above +24 rejected");
    rejects(withParam("output_trim_db", "13"), "OUT_OF_RANGE", "output_trim_db above +12 rejected");
    rejects(withParam("sp_input_gain_db", "30"), "UNKNOWN_ENUM", "sp_input_gain_db 30 rejected (not a step)");
    rejects(withParam("sp_input_gain_db", "1"), "UNKNOWN_ENUM", "sp_input_gain_db choice INDEX rejected (physical dB required)");
    rejects(withParam("mpc_input_gain", "\"HIGH\""), "UNKNOWN_ENUM", "mpc_input_gain unknown enum rejected");
    rejects(withParam("mpc_input_gain", "1"), "UNKNOWN_ENUM", "mpc_input_gain index rejected (enum name required)");
    rejects(withParam("plugin_bypass", "1"), "UNKNOWN_ENUM", "plugin_bypass non-bool rejected");
    rejects(withParam("sp_input_level_db", "\"6\""), "NON_FINITE_OR_MALFORMED", "string number rejected");
    { juce::var v = candidateToVar(demo()); v["product_parameters"].getDynamicObject()->setProperty("drive", 0.5); rejects(juce::JSON::toString(v), "UNKNOWN_KEY", "hidden parameter 'drive' rejected"); }
    { juce::var v = candidateToVar(demo()); v["product_parameters"].getDynamicObject()->setProperty("quantizer_rule", "FLOOR"); rejects(juce::JSON::toString(v), "UNKNOWN_KEY", "research key rejected"); }
    { juce::var v = candidateToVar(demo()); v["product_parameters"].getDynamicObject()->removeProperty("output_trim_db"); rejects(juce::JSON::toString(v), "MISSING_FIELD", "missing control rejected"); }
    { juce::var v = candidateToVar(demo()); v["authoring_metadata"].getDynamicObject()->setProperty("acceptance_status", "FACTORY"); rejects(juce::JSON::toString(v), "UNKNOWN_ENUM", "unknown acceptance status rejected"); }
    { juce::var v = candidateToVar(demo()); v["authoring_metadata"].getDynamicObject()->setProperty("secret_gain", 3.0); rejects(juce::JSON::toString(v), "UNKNOWN_KEY", "unknown metadata key rejected"); }
    { juce::var v = candidateToVar(demo()); v["authoring_metadata"].getDynamicObject()->setProperty("description", juce::String::repeatedString("x", CANDIDATE_MAX_BYTES)); rejects(juce::JSON::toString(v), "OVERSIZED", "oversized candidate rejected"); }
    // ---- partial-application guard: a record with a valid first half and an invalid last value changes nothing
    { Candidate out; out.params.sp_input_level_db = -3.0; auto json = withParam("plugin_bypass", "\"maybe\""); auto r = parseCandidate(json, out); CHECK(!r.ok && out.params.sp_input_level_db == -3.0 && isInit(ProductParameters::defaults()), "no partial application on invalid input"); }
    // ---- renders
    LabEngine lab; juce::AudioBuffer<double> src = synth(48000, 0.5, 0.5), o1, o2, o3, o4;
    auto c = demo();
    auto r1 = lab.render(src, 48000, c.params, o1); auto r2 = lab.render(src, 48000, c.params, o2);
    CHECK(r1.ok && r2.ok, "render ok");
    CHECK(r1.ok && r1.output_f64_sha256 == r2.output_f64_sha256 && r1.frames_out == r1.frames_in + r1.latency, "deterministic render (same candidate twice, bit-identical)");
    CHECK(r1.ok && r1.latency == 310, "latency reported through the plugin at 48 kHz = 310");
    { Candidate m = demo(); m.name = "other name"; m.category = "HEAVY"; m.meta.description = "different metadata"; m.meta.acceptance_status = "CANDIDATE"; m.meta.audition_notes = "n"; m.revision = 7; auto r3 = lab.render(src, 48000, m.params, o3); CHECK(r3.ok && r3.output_f64_sha256 == r1.output_f64_sha256, "candidate metadata does not alter DSP output"); }
    { ProductParameters q = c.params; q.interstage_level_db = 9.0; auto r4 = lab.render(src, 48000, q, o4); CHECK(r4.ok && r4.output_f64_sha256 != r1.output_f64_sha256, "different parameters give a different render"); }
    { ProductParameters q = ProductParameters::defaults(); juce::AudioBuffer<double> a, b; auto ra = lab.render(src, 48000, q, a); LabEngine lab2; auto rb = lab2.render(src, 48000, q, b); CHECK(ra.ok && rb.ok && ra.output_f64_sha256 == rb.output_f64_sha256, "same ProductParameters produce the same product output in two engine instances"); }
    { juce::AudioBuffer<double> a; ProductParameters q = c.params; q.plugin_bypass = true; auto ra = lab.render(src, 48000, q, a); double maxd = 0.0; for (int i = 0; i < src.getNumSamples(); ++i) for (int ch = 0; ch < 2; ++ch) maxd = std::max(maxd, std::fabs(a.getSample(ch, i + static_cast<int>(ra.latency)) - src.getSample(ch, i))); CHECK(ra.ok && maxd == 0.0, "bypassed render = latency-aligned original input (exact)"); }
    { Candidate heavy = demo(); heavy.params.sp_input_level_db = 12.0; heavy.params.sp_input_gain_db = 40; heavy.params.interstage_level_db = 24.0; juce::AudioBuffer<double> a; auto ra = lab.render(src, 48000, heavy.params, a); CHECK(ra.ok && (ra.clamps.sp_clip[0] > 0) && (ra.clamps.mpc_clip18[0] > 0), "clamp report counts converter clamps on a heavily driven render"); CHECK(ra.ok && ra.clamps.text().contains("Output over-range:"), "clamp report text present"); }
    { ProductParameters q = ProductParameters::defaults(); q.sp_input_level_db = 13.0; juce::AudioBuffer<double> a; auto ra = lab.render(src, 48000, q, a); CHECK(!ra.ok, "render refuses out-of-range parameters"); }
    { juce::AudioBuffer<double> a; auto ra = lab.render(src, 50000, c.params, a); CHECK(!ra.ok, "render refuses unsupported rate"); }
    // ---- effective values: the plugin's parameter mapping is what a host delivers; the stored values stay physical
    CHECK(r1.ok && std::fabs(r1.effective.v[0] - 6.0) < 1e-4 && r1.effective.v[1] == 20.0 && r1.effective.v[3] == 1.0 && std::fabs(r1.effective.v[4] + 6.0) < 1e-4, "effective host-mapped values match the candidate within float32 mapping precision");
    std::printf("preset_lab_test: %d passed, %d failed\n", passes, fails);
    return fails == 0 ? 0 : 1;
}
