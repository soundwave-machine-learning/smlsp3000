#include "PresetCandidate.h"
#include "track_a_assets_v1.hpp"
#include "smlsp3000/host_adapter.hpp"
#include <cmath>

namespace preset_lab {
namespace A = smlsp3000::assets_v1;
using smlsp3000::ProductParameters;

const juce::StringArray& categories() { static const juce::StringArray c{"UTILITY", "CLEAN", "SP CHARACTER", "MPC CHARACTER", "DUAL STAGE", "DRUMS", "BASS", "SAMPLE / DENSE", "HEAVY", "EXPERIMENTAL"}; return c; }
const juce::StringArray& acceptanceStatuses() { static const juce::StringArray s{"DRAFT", "AUDITIONED", "CANDIDATE", "REJECTED", "TOOL_DEMO"}; return s; }

static juce::String f17(double v) { char b[64]; std::snprintf(b, sizeof b, "%.17g", v); return b; }

juce::String nativeStateText(const ProductParameters& p) {
    juce::String s;
    s << "smlsp3000-state\n";
    s << "schema_version=" << A::CONTROLS_SCHEMA_VERSION << "\n";
    s << "controls=" << A::CONTROLS_ID << ";" << A::CONTROLS_SHA256 << "\n";
    s << "product_config=" << A::PRODUCT_CONFIG_ID << ";" << A::PRODUCT_CONFIG_VERSION << ";" << A::PRODUCT_CONFIG_SHA256 << "\n";
    s << "sp_asset=" << A::SP_ASSET_ID << ";" << A::SP_ASSET_VERSION << ";" << A::SP_MODEL_VERSION << ";" << A::SP_ASSET_SHA256 << "\n";
    s << "mpc_asset=" << A::MPC_ASSET_ID << ";" << A::MPC_ASSET_VERSION << ";" << A::MPC_MODEL_VERSION << ";" << A::MPC_ASSET_SHA256 << "\n";
    s << "sp_input_level_db=" << f17(p.sp_input_level_db) << "\n";
    s << "sp_input_gain_db=" << p.sp_input_gain_db << "\n";
    s << "interstage_level_db=" << f17(p.interstage_level_db) << "\n";
    s << "mpc_input_gain=" << smlsp3000::mpc_gain_name(p.mpc_input_gain) << "\n";
    s << "output_trim_db=" << f17(p.output_trim_db) << "\n";
    s << "plugin_bypass=" << (p.plugin_bypass ? "1" : "0") << "\n";
    return s;
}

ParseResult validateParameters(const ProductParameters& p) {
    ProductParameters tmp = ProductParameters::defaults();
    auto r = smlsp3000::Engine::parse_state(nativeStateText(p).toStdString(), tmp);
    ParseResult o; o.ok = r.ok; o.code = r.code; o.detail = r.detail; return o;
}

bool sameProductParameters(const ProductParameters& a, const ProductParameters& b) {
    return a.sp_input_level_db == b.sp_input_level_db && a.sp_input_gain_db == b.sp_input_gain_db && a.interstage_level_db == b.interstage_level_db
        && a.mpc_input_gain == b.mpc_input_gain && a.output_trim_db == b.output_trim_db && a.plugin_bypass == b.plugin_bypass;
}
bool isInit(const ProductParameters& p) { return sameProductParameters(p, ProductParameters::defaults()); }

juce::String utcNow() { return juce::Time::getCurrentTime().toISO8601(true); }
juce::String newCandidateId() { juce::Random r(juce::Time::currentTimeMillis()); juce::String s = "cand_"; for (int i = 0; i < 12; ++i) s << juce::String::toHexString(r.nextInt(16)); return s; }

static bool isIdent(const juce::String& s) { if (s.isEmpty() || s.length() > 64) return false; for (auto c : s) if (!(juce::CharacterFunctions::isLetterOrDigit(c) || c == '_' || c == '-')) return false; return true; }

static ParseResult fail(const char* code, const juce::String& detail) { ParseResult r; r.ok = false; r.code = code; r.detail = detail; return r; }

static bool onlyKeys(const juce::var& obj, const juce::StringArray& allowed, juce::String& offending) {
    auto* d = obj.getDynamicObject(); if (!d) return false;
    for (auto& p : d->getProperties()) if (!allowed.contains(p.name.toString())) { offending = p.name.toString(); return false; }
    return true;
}

ParseResult parseCandidate(const juce::String& jsonText, Candidate& out) {
    if (jsonText.getNumBytesAsUTF8() > CANDIDATE_MAX_BYTES) return fail("OVERSIZED", "candidate text exceeds " + juce::String(CANDIDATE_MAX_BYTES) + " bytes");
    juce::var root; auto res = juce::JSON::parse(jsonText, root);
    if (res.failed() || root.getDynamicObject() == nullptr) return fail("MALFORMED_JSON", res.failed() ? res.getErrorMessage() : juce::String("top level must be a JSON object"));
    juce::String bad;
    if (!onlyKeys(root, {"format", "schema", "id", "name", "category", "revision", "product_parameters", "authoring_metadata"}, bad)) return fail("UNKNOWN_KEY", bad);
    if (root["format"].toString() != CANDIDATE_FORMAT) return fail("NOT_A_CANDIDATE", "format must be " + juce::String(CANDIDATE_FORMAT));
    if (!root["schema"].isInt() && !root["schema"].isInt64()) return fail("MALFORMED_SCHEMA", "schema must be an integer");
    const int schema = static_cast<int>(root["schema"]);
    if (schema > CANDIDATE_SCHEMA) return fail("UNSUPPORTED_SCHEMA_VERSION", "schema " + juce::String(schema) + " is newer than " + juce::String(CANDIDATE_SCHEMA) + "; no migration exists");
    if (schema != CANDIDATE_SCHEMA) return fail("UNSUPPORTED_SCHEMA_VERSION", "schema " + juce::String(schema) + " is not supported");
    Candidate c;
    c.id = root["id"].toString(); if (!root["id"].isString() || !isIdent(c.id)) return fail("BAD_ID", "id must be 1..64 characters of [A-Za-z0-9_-]");
    c.name = root["name"].toString(); if (!root["name"].isString() || c.name.trim().isEmpty() || c.name.length() > 128) return fail("BAD_NAME", "name must be a non-empty string (<= 128 characters)");
    c.category = root["category"].toString(); if (!root["category"].isString() || !categories().contains(c.category)) return fail("UNKNOWN_CATEGORY", c.category);
    if (!(root["revision"].isInt() || root["revision"].isInt64()) || static_cast<int>(root["revision"]) < 1) return fail("BAD_REVISION", "revision must be an integer >= 1");
    c.revision = static_cast<int>(root["revision"]);
    const juce::var pp = root["product_parameters"]; if (pp.getDynamicObject() == nullptr) return fail("MISSING_FIELD", "product_parameters");
    if (!onlyKeys(pp, {"sp_input_level_db", "sp_input_gain_db", "interstage_level_db", "mpc_input_gain", "output_trim_db", "plugin_bypass"}, bad)) return fail("UNKNOWN_KEY", "product_parameters." + bad + " (research or hidden parameters are never accepted)");
    for (const char* k : {"sp_input_level_db", "sp_input_gain_db", "interstage_level_db", "mpc_input_gain", "output_trim_db", "plugin_bypass"}) if (!pp.hasProperty(k)) return fail("MISSING_FIELD", juce::String("product_parameters.") + k);
    auto num = [](const juce::var& v, double& d) { if (v.isDouble() || v.isInt() || v.isInt64()) { d = static_cast<double>(v); return std::isfinite(d); } return false; };
    double d = 0.0; ProductParameters p = ProductParameters::defaults();
    if (!num(pp["sp_input_level_db"], d)) return fail("NON_FINITE_OR_MALFORMED", "sp_input_level_db"); p.sp_input_level_db = d;
    if (!num(pp["sp_input_gain_db"], d) || d != std::floor(d)) return fail("UNKNOWN_ENUM", "sp_input_gain_db must be one of 0, 20, 40 (physical dB step)"); p.sp_input_gain_db = static_cast<int>(d);
    if (!num(pp["interstage_level_db"], d)) return fail("NON_FINITE_OR_MALFORMED", "interstage_level_db"); p.interstage_level_db = d;
    if (!pp["mpc_input_gain"].isString() || !smlsp3000::parse_mpc_gain(pp["mpc_input_gain"].toString().toStdString(), p.mpc_input_gain)) return fail("UNKNOWN_ENUM", "mpc_input_gain must be LO, MID or HI");
    if (!num(pp["output_trim_db"], d)) return fail("NON_FINITE_OR_MALFORMED", "output_trim_db"); p.output_trim_db = d;
    if (!pp["plugin_bypass"].isBool()) return fail("UNKNOWN_ENUM", "plugin_bypass must be true or false"); p.plugin_bypass = static_cast<bool>(pp["plugin_bypass"]);
    auto v = validateParameters(p); if (!v.ok) return v;                 // the core's own range/enum policy (OUT_OF_RANGE, UNKNOWN_ENUM, ...)
    c.params = p;
    const juce::var am = root["authoring_metadata"]; if (am.getDynamicObject() == nullptr) return fail("MISSING_FIELD", "authoring_metadata");
    if (!onlyKeys(am, {"author", "description", "audition_notes", "clamp_observations", "engineering_note", "source_material", "acceptance_status", "input_peak", "output_peak", "created_utc", "modified_utc", "tool_version", "native_core_version", "adapter_version"}, bad)) return fail("UNKNOWN_KEY", "authoring_metadata." + bad);
    auto str = [&](const char* k, juce::String& dst) -> bool { if (!am.hasProperty(k)) return true; if (!am[k].isString()) return false; dst = am[k].toString(); return true; };
    for (auto [k, dst] : std::initializer_list<std::pair<const char*, juce::String*>>{{"author", &c.meta.author}, {"description", &c.meta.description}, {"audition_notes", &c.meta.audition_notes}, {"clamp_observations", &c.meta.clamp_observations}, {"engineering_note", &c.meta.engineering_note}, {"created_utc", &c.meta.created_utc}, {"modified_utc", &c.meta.modified_utc}, {"tool_version", &c.meta.tool_version}, {"native_core_version", &c.meta.native_core_version}, {"adapter_version", &c.meta.adapter_version}})
        if (!str(k, *dst)) return fail("MALFORMED_METADATA", juce::String("authoring_metadata.") + k + " must be a string");
    if (am.hasProperty("acceptance_status")) { if (!am["acceptance_status"].isString() || !acceptanceStatuses().contains(am["acceptance_status"].toString())) return fail("UNKNOWN_ENUM", "acceptance_status"); c.meta.acceptance_status = am["acceptance_status"].toString(); }
    if (am.hasProperty("source_material")) { if (!am["source_material"].isArray()) return fail("MALFORMED_METADATA", "source_material must be an array of strings"); for (auto& e : *am["source_material"].getArray()) { if (!e.isString()) return fail("MALFORMED_METADATA", "source_material entries must be strings"); c.meta.source_material.add(e.toString()); } }
    for (auto [k, dst] : std::initializer_list<std::pair<const char*, double*>>{{"input_peak", &c.meta.input_peak}, {"output_peak", &c.meta.output_peak}})
        if (am.hasProperty(k)) { if (!num(am[k], d)) return fail("MALFORMED_METADATA", juce::String("authoring_metadata.") + k + " must be a finite number"); *dst = d; }
    out = c;                                                            // only now: nothing applied on any earlier rejection
    ParseResult ok; ok.ok = true; ok.code = "OK"; return ok;
}

juce::var candidateToVar(const Candidate& c) {
    auto* root = new juce::DynamicObject();
    root->setProperty("format", CANDIDATE_FORMAT); root->setProperty("schema", CANDIDATE_SCHEMA);
    root->setProperty("id", c.id); root->setProperty("name", c.name); root->setProperty("category", c.category); root->setProperty("revision", c.revision);
    auto* pp = new juce::DynamicObject();
    pp->setProperty("sp_input_level_db", c.params.sp_input_level_db); pp->setProperty("sp_input_gain_db", c.params.sp_input_gain_db);
    pp->setProperty("interstage_level_db", c.params.interstage_level_db); pp->setProperty("mpc_input_gain", juce::String(smlsp3000::mpc_gain_name(c.params.mpc_input_gain)));
    pp->setProperty("output_trim_db", c.params.output_trim_db); pp->setProperty("plugin_bypass", c.params.plugin_bypass);
    root->setProperty("product_parameters", juce::var(pp));
    auto* am = new juce::DynamicObject();
    am->setProperty("author", c.meta.author); am->setProperty("description", c.meta.description); am->setProperty("audition_notes", c.meta.audition_notes);
    am->setProperty("clamp_observations", c.meta.clamp_observations); am->setProperty("engineering_note", c.meta.engineering_note);
    juce::Array<juce::var> src; for (auto& s : c.meta.source_material) src.add(s); am->setProperty("source_material", src);
    am->setProperty("acceptance_status", c.meta.acceptance_status); am->setProperty("input_peak", c.meta.input_peak); am->setProperty("output_peak", c.meta.output_peak);
    am->setProperty("created_utc", c.meta.created_utc); am->setProperty("modified_utc", c.meta.modified_utc);
    am->setProperty("tool_version", c.meta.tool_version.isEmpty() ? juce::String(TOOL_VERSION) : c.meta.tool_version);
    am->setProperty("native_core_version", c.meta.native_core_version.isEmpty() ? juce::String(smlsp3000::NATIVE_IMPLEMENTATION_VERSION) : c.meta.native_core_version);
    am->setProperty("adapter_version", c.meta.adapter_version.isEmpty() ? juce::String(smlsp3000::HOST_ADAPTER_VERSION) : c.meta.adapter_version);
    root->setProperty("authoring_metadata", juce::var(am));
    return juce::var(root);
}

juce::String serializeCandidate(const Candidate& c) { return juce::JSON::toString(candidateToVar(c), false) + "\n"; }

ParseResult loadCandidateFile(const juce::File& f, Candidate& out) {
    if (!f.existsAsFile()) return fail("IO", "file not found: " + f.getFullPathName());
    if (f.getSize() > CANDIDATE_MAX_BYTES) return fail("OVERSIZED", "file exceeds " + juce::String(CANDIDATE_MAX_BYTES) + " bytes");
    return parseCandidate(f.loadFileAsString(), out);
}

bool saveCandidateFile(const juce::File& f, const Candidate& c) {
    juce::TemporaryFile tmp(f);
    if (!tmp.getFile().replaceWithText(serializeCandidate(c))) return false;
    return tmp.overwriteTargetFileWithTemporary();
}

}  // namespace preset_lab
