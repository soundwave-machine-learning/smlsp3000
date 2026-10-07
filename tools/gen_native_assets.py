#!/usr/bin/env python3
"""Generate native/generated/track_a_assets_v1.hpp from the versioned JSON assets, research configurations,
product configuration and frozen product controls (OWN-DEC-014/020).

The native core consumes every machine value, research switch and product range from this header, so the DSP
code contains no literal coefficient, gain, clamp or rate (docs/ARCHITECTURE.md provisional-asset interface).
The canonical SHA-256 of every source record is embedded; tests/test_native_assets.py fails if the header
drifts from the JSON. Run from the repository root: python3 tools/gen_native_assets.py [--check]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from smlsp3000.hashing import sha256_bytes  # noqa: E402
from smlsp3000.reference.assets import ASSET_DIR, canonical_bytes, load_json  # noqa: E402

OUT = ROOT / "native" / "generated" / "track_a_assets_v1.hpp"


def flit(x: float) -> str:
    r = repr(float(x))
    if "e" not in r and "." not in r and "inf" not in r and "nan" not in r:
        r += ".0"
    return r


def cstr(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def generate() -> str:
    sp = load_json(ASSET_DIR / "sp1200_provisional_v1.json"); sps = sha256_bytes(canonical_bytes(sp))
    spr = load_json(ASSET_DIR / "research_config_sp_track_a_v1.json"); sprs = sha256_bytes(canonical_bytes(spr))
    mpc = load_json(ASSET_DIR / "mpc3000_provisional_v1.json"); mpcs = sha256_bytes(canonical_bytes(mpc))
    mpr = load_json(ASSET_DIR / "research_config_mpc_track_a_v1.json"); mprs = sha256_bytes(canonical_bytes(mpr))
    pc = load_json(ASSET_DIR / "product_config_track_a_v1.json"); pcs = sha256_bytes(canonical_bytes(pc))
    cc = load_json(ASSET_DIR / "research_config_cascade_track_a_v1.json"); ccs = sha256_bytes(canonical_bytes(cc))
    ctl = load_json(ASSET_DIR / "product_controls_v1.json"); ctls = sha256_bytes(canonical_bytes(ctl))
    v = lambda a, k: a["values"][k]["value"]
    sw, mw = spr["switches"], mpr["switches"]
    L = []
    w = L.append
    w("// GENERATED FILE — do not edit. Source: smlsp3000/reference/assets/*.json via tools/gen_native_assets.py")
    w("// Track A provisional assets (OWN-DEC-001..013), research switches at the Sprint 5 checkpoint, product configuration and")
    w("// frozen product controls (OWN-DEC-020). Every value is UNVALIDATED AGAINST HARDWARE. Changing a JSON source requires regeneration.")
    w("#pragma once")
    w("#include <cstdint>")
    w("namespace smlsp3000::assets_v1 {")
    w(f"inline constexpr const char* SP_ASSET_ID = {cstr(sp['asset_id'])};")
    w(f"inline constexpr const char* SP_ASSET_VERSION = {cstr(sp['version'])};")
    w(f"inline constexpr const char* SP_MODEL_VERSION = {cstr(sp['model_version'])};")
    w(f"inline constexpr const char* SP_ASSET_SHA256 = {cstr(sps)};")
    w(f"inline constexpr const char* SP_RESEARCH_CONFIG_ID = {cstr(spr['config_id'])};")
    w(f"inline constexpr const char* SP_RESEARCH_SHA256 = {cstr(sprs)};")
    r = v(sp, "sp_rate_hz"); w(f"inline constexpr std::int64_t SP_RATE_NUM = {int(r['numerator'])};"); w(f"inline constexpr std::int64_t SP_RATE_DEN = {int(r['denominator'])};")
    w(f"inline constexpr int SP_WORD_BITS = {int(v(sp,'word_bits'))};")
    cr = v(sp, "code_range"); w(f"inline constexpr int SP_CODE_MIN = {int(cr['min'])};"); w(f"inline constexpr int SP_CODE_MAX = {int(cr['max'])};")
    w(f"inline constexpr const char* SP_QUANTIZER_RULE_DEFAULT = {cstr(v(sp,'quantizer_rule_default'))};")
    w(f"inline constexpr double SP_QUANTIZER_OFFSET_CODES_ASSET = {flit(v(sp,'quantizer_offset_codes'))};")
    steps = v(sp, "input_gain_steps_db"); w(f"inline constexpr int SP_INPUT_GAIN_STEPS_DB[{len(steps)}] = {{{', '.join(str(int(s)) for s in steps)}}};")
    w(f"inline constexpr const char* SP_R2_ANALOG_CLAMP = {cstr(v(sp,'r2_analog_clamp'))};")
    w(f"inline constexpr const char* SP_R3_STRATEGY = {cstr(v(sp,'r3_strategy'))};")
    w(f"inline constexpr double SP_HOLD_FRACTION = {flit(v(sp,'hold_fraction'))};")
    w(f"inline constexpr double SP_DAC_FULL_SCALE_NORMALIZED = {flit(v(sp,'dac_full_scale_normalized'))};")
    w(f"inline constexpr double SP_R9_OUTPUT_GAIN_NORMALIZED = {flit(v(sp,'r9_output_gain_normalized'))};")
    w(f"inline constexpr const char* SP_R9_COUPLING_POLE = {cstr(v(sp,'r9_coupling_pole'))};")
    routes = v(sp, "output_routes"); pop = [k for k, r in routes.items() if r["status"] == "POPULATED"]
    w(f"inline constexpr const char* SP_ROUTES_POPULATED[{len(pop)}] = {{{', '.join(cstr(p) for p in pop)}}};")
    allr = list(routes.keys()); w(f"inline constexpr const char* SP_ROUTES_KNOWN[{len(allr)}] = {{{', '.join(cstr(p) for p in allr)}}};")
    w(f"inline constexpr const char* SP_VOLTS_PER_NORMALIZED_UNIT = {cstr(str(v(sp,'volts_per_normalized_unit')))};")
    # SP research switches (checkpoint)
    w(f"inline constexpr const char* SP_RC_QUANTIZER_RULE = {cstr(sw['quantizer_rule'])};")
    w(f"inline constexpr double SP_RC_QUANTIZER_OFFSET_CODES = {flit(sw['quantizer_offset_codes'])};")
    w(f"inline constexpr bool SP_RC_QUANTIZER_BYPASS = {'true' if sw['quantizer_bypass_diagnostic'] else 'false'};")
    w(f"inline constexpr const char* SP_RC_R3_STRATEGY = {cstr(sw['r3_strategy'])};")
    w(f"inline constexpr double SP_RC_HOLD_FRACTION = {flit(sw['hold_fraction'])};")
    w(f"inline constexpr int SP_RC_PROXY_OVERSAMPLING = {int(sw['proxy_oversampling'])};")
    w(f"inline constexpr int SP_RC_LOBES_PER_SIDE = {int(sw['r1_r16_kernel']['lobes_per_side'])};")
    w(f"inline constexpr double SP_RC_LOWPASS_KAISER_BETA = {flit(sw['r1_r16_kernel']['kaiser_beta'])};")
    w(f"inline constexpr int SP_RC_SAMPLER_HALF_WIDTH_HOST = {int(sw['sampler_half_width_host_samples'])};")
    w(f"inline constexpr int SP_RC_HOLD_KERNEL_HALF_WIDTH_HOST = {int(sw['hold_kernel_half_width_host_samples'])};")
    w(f"inline constexpr double SP_RC_INTERP_KAISER_BETA = {flit(sw['interpolation_kaiser_beta'])};")
    w(f"inline constexpr bool SP_RC_SLOT_SKEW_ENABLED = {'true' if sw['slot_skew_enabled'] else 'false'};")
    w(f"inline constexpr bool SP_RC_CAPTURE_OFFSET_ENABLED = {'true' if sw['capture_offset_enabled'] else 'false'};")
    w(f"inline constexpr bool SP_RC_DIAGNOSTIC_TAPS = {'true' if sw['diagnostic_taps'] else 'false'};")
    # MPC
    w(f"inline constexpr const char* MPC_ASSET_ID = {cstr(mpc['asset_id'])};")
    w(f"inline constexpr const char* MPC_ASSET_VERSION = {cstr(mpc['version'])};")
    w(f"inline constexpr const char* MPC_MODEL_VERSION = {cstr(mpc['model_version'])};")
    w(f"inline constexpr const char* MPC_ASSET_SHA256 = {cstr(mpcs)};")
    w(f"inline constexpr const char* MPC_RESEARCH_CONFIG_ID = {cstr(mpr['config_id'])};")
    w(f"inline constexpr const char* MPC_RESEARCH_SHA256 = {cstr(mprs)};")
    r = v(mpc, "mpc_rate_hz"); w(f"inline constexpr std::int64_t MPC_RATE_NUM = {int(r['numerator'])};"); w(f"inline constexpr std::int64_t MPC_RATE_DEN = {int(r['denominator'])};")
    w(f"inline constexpr int MPC_CONVERTER_BITS = {int(v(mpc,'converter_bits'))};"); w(f"inline constexpr int MPC_STORAGE_BITS = {int(v(mpc,'storage_bits'))};")
    cr = v(mpc, "converter_code_range"); w(f"inline constexpr int MPC_C18_MIN = {int(cr['min'])};"); w(f"inline constexpr int MPC_C18_MAX = {int(cr['max'])};")
    sr = v(mpc, "storage_code_range"); w(f"inline constexpr int MPC_C16_MIN = {int(sr['min'])};"); w(f"inline constexpr int MPC_C16_MAX = {int(sr['max'])};")
    w(f"inline constexpr const char* MPC_ADC_CODE_REPRESENTATION = {cstr(v(mpc,'adc_code_representation'))};")
    w(f"inline constexpr const char* MPC_REDUCTION_RULE_DEFAULT = {cstr(v(mpc,'reduction_rule_default'))};")
    w(f"inline constexpr const char* MPC_R14_ARITHMETIC = {cstr(v(mpc,'r14_arithmetic'))};")
    gs = v(mpc, "input_gain_steps"); names = list(gs.keys())
    w(f"inline constexpr const char* MPC_INPUT_GAIN_NAMES[{len(names)}] = {{{', '.join(cstr(n) for n in names)}}};")
    w(f"inline constexpr int MPC_INPUT_GAIN_RELATIVE_DB[{len(names)}] = {{{', '.join(str(int(gs[n]['relative_gain_db'])) for n in names)}}};")
    w(f"inline constexpr const char* MPC_RECORD_LEVEL_LAW = {cstr(v(mpc,'record_level_law'))};")
    for key in ("r11_analog_clamp", "r11_coupling_pole", "r12_strategy", "r15_strategy", "de_emphasis", "r15_coupling_pole"):
        w(f"inline constexpr const char* MPC_{key.upper()} = {cstr(v(mpc,key))};")
    routes = v(mpc, "output_routes")
    for k, rr in routes.items():
        w(f"inline constexpr const char* MPC_ROUTE_STATUS_{k} = {cstr(rr['status'])};")
    allr = list(routes.keys()); w(f"inline constexpr const char* MPC_ROUTES_KNOWN[{len(allr)}] = {{{', '.join(cstr(p) for p in allr)}}};")
    w(f"inline constexpr double MPC_DAC_FULL_SCALE_NORMALIZED = {flit(v(mpc,'dac_full_scale_normalized'))};")
    w(f"inline constexpr const char* MPC_VOLTS_PER_NORMALIZED_UNIT = {cstr(str(v(mpc,'volts_per_normalized_unit')))};")
    w(f"inline constexpr const char* MPC_RC_REDUCTION_RULE = {cstr(mw['reduction_rule'])};")
    w(f"inline constexpr const char* MPC_RC_R12_STRATEGY = {cstr(mw['r12_strategy'])};")
    w(f"inline constexpr const char* MPC_RC_R15_STRATEGY = {cstr(mw['r15_strategy'])};")
    w(f"inline constexpr const char* MPC_RC_R14_STRATEGY = {cstr(mw['r14_strategy'])};")
    w(f"inline constexpr bool MPC_RC_QUANT_BYPASS = {'true' if mw['converter_quantization_bypass_diagnostic'] else 'false'};")
    w(f"inline constexpr const char* MPC_RC_DE_EMPHASIS = {cstr(mw['de_emphasis'])};")
    w(f"inline constexpr int MPC_RC_PROXY_OVERSAMPLING = {int(mw['proxy_oversampling'])};")
    w(f"inline constexpr int MPC_RC_LOBES_PER_SIDE = {int(mw['r1_r16_kernel']['lobes_per_side'])};")
    w(f"inline constexpr double MPC_RC_LOWPASS_KAISER_BETA = {flit(mw['r1_r16_kernel']['kaiser_beta'])};")
    w(f"inline constexpr int MPC_RC_R12_HALF_WIDTH_HOST = {int(mw['r12_lowpass_half_width_host_samples'])};")
    w(f"inline constexpr double MPC_RC_R12_KAISER_BETA = {flit(mw['r12_lowpass_kaiser_beta'])};")
    w(f"inline constexpr int MPC_RC_SAMPLER_HALF_WIDTH_HOST = {int(mw['sampler_half_width_host_samples'])};")
    w(f"inline constexpr int MPC_RC_RECON_HALF_WIDTH_MACHINE = {int(mw['reconstruction_half_width_machine_samples'])};")
    w(f"inline constexpr double MPC_RC_INTERP_KAISER_BETA = {flit(mw['interpolation_kaiser_beta'])};")
    w(f"inline constexpr bool MPC_RC_DIAGNOSTIC_TAPS = {'true' if mw['diagnostic_taps'] else 'false'};")
    # product config
    w(f"inline constexpr const char* PRODUCT_CONFIG_ID = {cstr(pc['config_id'])};"); w(f"inline constexpr const char* PRODUCT_CONFIG_VERSION = {cstr(pc['version'])};"); w(f"inline constexpr const char* PRODUCT_CONFIG_SHA256 = {cstr(pcs)};")
    w(f"inline constexpr const char* PRODUCT_PATH = {cstr(pc['product_path']['selected'])};")
    w(f"inline constexpr const char* PRODUCT_SP_OUTPUT_PATH = {cstr(pc['routes']['sp_output_path'])};"); w(f"inline constexpr const char* PRODUCT_MPC_OUTPUT_ROUTE = {cstr(pc['routes']['mpc_output_route'])};")
    w(f"inline constexpr double PRODUCT_INTERSTAGE_DEFAULT_DB = {flit(pc['interstage']['default_db'])};")
    w(f"inline constexpr double PRODUCT_INTERSTAGE_RESEARCH_MIN_DB = {flit(pc['interstage']['research_range_db'][0])};"); w(f"inline constexpr double PRODUCT_INTERSTAGE_RESEARCH_MAX_DB = {flit(pc['interstage']['research_range_db'][1])};")
    w(f"inline constexpr const char* PRODUCT_CHAIN_MODE_DEFAULT = {cstr(pc['chain_modes']['product_default'])};")
    w(f"inline constexpr const char* CASCADE_RESEARCH_CONFIG_ID = {cstr(cc['config_id'])};"); w(f"inline constexpr const char* CASCADE_RESEARCH_SHA256 = {cstr(ccs)};")
    w(f"inline constexpr bool CASCADE_RC_REVERSE_ORDER_RESEARCH = {'true' if cc['switches']['reverse_order_research'] else 'false'};")
    # controls
    c = ctl["controls"]
    w(f"inline constexpr const char* CONTROLS_ID = {cstr(ctl['controls_id'])};"); w(f"inline constexpr int CONTROLS_SCHEMA_VERSION = {int(ctl['schema_version'])};"); w(f"inline constexpr const char* CONTROLS_SHA256 = {cstr(ctls)};")
    for name in ("sp_input_level_db", "interstage_level_db", "output_trim_db"):
        u = name.upper(); w(f"inline constexpr double CTRL_{u}_MIN = {flit(c[name]['min'])};"); w(f"inline constexpr double CTRL_{u}_MAX = {flit(c[name]['max'])};"); w(f"inline constexpr double CTRL_{u}_DEFAULT = {flit(c[name]['default'])};")
    w(f"inline constexpr int CTRL_SP_INPUT_GAIN_DEFAULT_DB = {int(c['sp_input_gain']['default'])};")
    w(f"inline constexpr const char* CTRL_MPC_INPUT_GAIN_DEFAULT = {cstr(c['mpc_input_gain']['default'])};")
    w(f"inline constexpr bool CTRL_PLUGIN_BYPASS_DEFAULT = {'true' if c['plugin_bypass']['default'] else 'false'};")
    w(f"inline constexpr double CTRL_RAMP_MS = {flit(ctl['ramp_ms'])};")
    pp = ctl["product_profile"]
    w(f"inline constexpr double PROFILE_MPC_RECORD_LEVEL_DB_FIXED = {flit(pp['mpc_record_level_db_internal_fixed'])};")
    w(f"inline constexpr const char* PROFILE_REDUCTION_RULE = {cstr(pp['reduction_rule'])};"); w(f"inline constexpr const char* PROFILE_QUANTIZER_RULE = {cstr(pp['quantizer_rule'])};")
    w(f"inline constexpr const char* PROFILE_CALIBRATION_MODE = {cstr(pp['calibration_mode'])};")
    w("}  // namespace smlsp3000::assets_v1")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    text = generate()
    if "--check" in sys.argv:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        print("UP TO DATE" if cur == text else "DRIFT"); sys.exit(0 if cur == text else 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8"); print(f"wrote {OUT.relative_to(ROOT)} ({len(text)} bytes)")
