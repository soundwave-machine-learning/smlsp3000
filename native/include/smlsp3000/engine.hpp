// SML SP-3000 native production core (Track A, OWN-DEC-014..023): framework-independent, float64, no I/O,
// no allocation/locks in process(). Composition and numerics follow the Python reference (cascade-reference-impl-1.0.0).
// Everything modelled is UNVALIDATED AGAINST HARDWARE; this is a software product inspired by and informed by
// documented SP-1200 / MPC3000 architecture, not an emulation, not hardware matched, not measured.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include "smlsp3000/kernels.hpp"
#include "smlsp3000/mpc_core.hpp"
#include "smlsp3000/sp_core.hpp"
#include "smlsp3000/streaming.hpp"

namespace smlsp3000 {

inline constexpr const char* NATIVE_IMPLEMENTATION_VERSION = "smlsp3000-native-core-1.0.0";
inline constexpr std::size_t MAX_BLOCK_LIMIT = 8192;          // owner-set preallocation bound (OWN-DEC-019)
inline constexpr std::size_t MAX_EVENTS_PER_CALL = 256;        // bounded parameter event schedule

enum class ChainMode : int { CASCADE = 0, SP_ONLY = 1, MPC_ONLY = 2, BOTH_MACHINE_BYPASSED = 3 };
enum class QuantizerRule : int { ROUND_NEAREST = 0, FLOOR = 1 };
enum class ReductionRule : int { ROUND_NEAREST = 0, TRUNCATION = 1 };
enum class MpcInputGain : int { LO = 0, MID = 1, HI = 2 };
enum class ParamId : int { SP_INPUT_LEVEL_DB = 0, SP_INPUT_GAIN_DB = 1, INTERSTAGE_LEVEL_DB = 2, MPC_INPUT_GAIN = 3, OUTPUT_TRIM_DB = 4, PLUGIN_BYPASS = 5 };

const char* chain_mode_name(ChainMode m);
const char* mpc_gain_name(MpcInputGain g);
bool parse_chain_mode(std::string_view s, ChainMode& out);
bool parse_mpc_gain(std::string_view s, MpcInputGain& out);

// PRODUCT PARAMETERS (schema v1 controls) + profile-fixed fields (not stored in state; research tools may change them).
struct ProductParameters {
    double sp_input_level_db = 0.0; int sp_input_gain_db = 0; double interstage_level_db = 0.0; MpcInputGain mpc_input_gain = MpcInputGain::LO;
    double output_trim_db = 0.0; bool plugin_bypass = false;
    // profile-fixed in product state v1
    ChainMode chain_mode = ChainMode::CASCADE; double mpc_record_level_db = 0.0;
    std::string sp_output_path = "NONE_CH7_8", mpc_output_route = "MAIN_LR"; bool physical_calibration = false;
    static ProductParameters defaults();
};

// RESEARCH CONFIGURATION (hypothesis switches; checkpoint values from the generated asset header; never in product state)
struct ResearchConfiguration {
    QuantizerRule quantizer_rule = QuantizerRule::ROUND_NEAREST; double quantizer_offset_codes = 0.0; bool quantizer_bypass = false;
    ReductionRule reduction_rule = ReductionRule::ROUND_NEAREST; bool converter_quant_bypass = false;
    int proxy_oversampling = 8; int lobes = 48; double lp_beta = 9.0;
    int sp_hw_s_host = 4, sp_hw_z_host = 4; double sp_interp_beta = 12.0;
    int r12_half_host = 62; double r12_beta = 9.0; int mpc_hw_s_host = 4, hw_r = 128; double mpc_interp_beta = 12.0;
    bool slot_skew_enabled = false, capture_offset_enabled = false, reverse_order_research = false;
    bool exact_reference_order = false;   // diagnostic: evaluate every linear stage separately in the reference's arithmetic order (slower); false = composed operator tables (production)
    static ResearchConfiguration checkpoint();   // the Sprint 5 checkpoint values (generated header)
};

struct ParamEvent { ParamId id; std::int64_t offset; double value; };   // offset: host sample within the call; value: dB / enum index / 0|1

struct PrepareResult { bool ok = false; std::string code, detail; };

struct PreparedInfo {
    int host_rate = 0, proxy_rate = 0, L = 0, channels = 0; std::size_t max_block = 0;
    ChainMode chain_mode = ChainMode::CASCADE; bool reverse_order_research = false;
    std::int64_t latency_host = 0, r1_proxy = 0, sp_core_proxy = 0, mpc_core_proxy = 0, r16_proxy = 0;
    std::int64_t sp_per_num = 0, sp_per_den = 0, mpc_per_num = 0, mpc_per_den = 0, mpc_D15 = 0, mpc_r12_half = 0;
    std::size_t lowpass_taps = 0, r12_taps = 0; double lowpass_dc_residual = 0.0, r12_dc_residual = 0.0, step_truncation_residual = 0.0;
    double sp_line_bound_relative = 0.0, mpc_line_bound_relative = 0.0;
    std::int64_t ramp_proxy_samples = 0, ramp_host_samples = 0, event_offset_r2_proxy = 0, event_offset_r10_proxy = 0;
    std::string sp_asset_sha256, mpc_asset_sha256, product_config_sha256, controls_sha256, version;
    bool exact_reference_order = false;
};

struct ChannelMeters { double host_input_peak = 0.0, sp_core_input_peak = 0.0, mpc_core_input_peak = 0.0, output_peak = 0.0; std::int64_t sp_clip = 0, mpc_clip18 = 0, mpc_clamp16 = 0; };
struct Meters { std::vector<ChannelMeters> channel; std::int64_t nonfinite_input_samples = 0, faults = 0, events_rejected = 0; bool fault_latched = false; };

struct StateLoadResult { bool ok = false; std::string code, detail; };

// linear-in-dB ramp advanced per sample of its own clock domain; pending events by absolute sample index
class GainRamp {
public:
    void configure(double initial_db, std::int64_t ramp_len);
    void reset(double initial_db);
    bool schedule(std::int64_t at, double target_db);        // false if the bounded queue is full
    void set_target_now(double target_db) { pending_n_ = 0; start(target_db); }
    double advance();                                         // gain for the current sample; then clock++
    double target_db() const { return target_db_; }
    double current_db() const { return cur_db_; }
    std::int64_t clock() const { return clock_; }
    bool ramping() const { return remaining_ > 0; }
private:
    void start(double target_db);
    double gain_of(double db) const;
    double target_db_ = 0.0, cur_db_ = 0.0, step_db_ = 0.0, gain_ = 1.0; std::int64_t remaining_ = 0, ramp_len_ = 0, clock_ = 0;
    struct Pending { std::int64_t at; double value; };
    std::array<Pending, 64> pending_{}; int pending_n_ = 0;
};

// discrete switch with event timing (no interpolation)
class Switch {
public:
    void reset(double v) { value_ = v; pending_n_ = 0; clock_ = 0; }
    bool schedule(std::int64_t at, double v);
    double advance();
    double value() const { return value_; }
private:
    double value_ = 0.0; std::int64_t clock_ = 0; struct Pending { std::int64_t at; double value; }; std::array<Pending, 64> pending_{}; int pending_n_ = 0;
};

class Engine {
public:
    PrepareResult prepare(int host_rate, int channels, std::size_t max_block, const ProductParameters& product, const ResearchConfiguration* research = nullptr);
    bool prepared() const { return prepared_; }
    void reset();                                              // stream start: clears state, snaps ramps to the configured values, clears meters
    void update_product_targets(const ProductParameters& p);   // NON-REALTIME (before reset/prepare): adopt the six control values as the configured values (ramps snap at the next reset)
    std::int64_t latency() const { return info_.latency_host; }
    const PreparedInfo& info() const { return info_; }
    // planar float64 in/out; frames may be 0..any (internal chunking at max_block); events sorted by offset (0 <= offset < frames)
    // returns the number of fault events raised during this call (0 = none)
    int process(const double* const* in, double* const* out, std::size_t frames, const ParamEvent* events = nullptr, std::size_t n_events = 0);
    const Meters& meters() const { return meters_; }
    void reset_meters();
    const ProductParameters& product() const { return product_; }
    // state v1 (non-audio thread): product controls + asset identity; research never serialized
    std::string serialize_state() const { return serialize_state_with_bypass(product_.plugin_bypass); }
    std::string serialize_state_with_bypass(bool plugin_bypass) const;   // host adapters own the bypass crossfade; the stored value is theirs
    static StateLoadResult parse_state(std::string_view text, ProductParameters& out);   // out keeps its profile-fixed fields
    // offline diagnostics only
    void set_tap_sinks(int channel, TapSink* sp_codes, TapSink* mpc_c18, TapSink* mpc_c16);
    const std::vector<double>& lowpass_taps() const { return h_lp_; }
    const std::vector<double>& r12_taps() const { return h_r12_; }
    const TapTable& sp_sampler_table() const { return sp_taps_; }
    const TapTable& mpc_sampler_table() const { return mpc_staps_; }
    const TapTable& mpc_recon_table() const { return mpc_rtaps_; }
    const StepTable& sp_step_table() const { return step_; }
private:
    void process_chunk(const double* const* in, double* const* out, std::size_t n, const ParamEvent* ev, std::size_t n_ev, std::int64_t host_abs0);
    void snap_params();
    bool prepared_ = false; ProductParameters product_; ResearchConfiguration research_; PreparedInfo info_;
    int channels_ = 0, L_ = 1; std::size_t max_block_ = 0;
    std::vector<double> h_lp_, h_r12_; TapTable sp_taps_, mpc_staps_, mpc_rtaps_; StepTable step_;
    std::vector<PolyphaseUpsampler> up_; std::vector<Decimator> down_; std::vector<SPCore> sp_; std::vector<MPCCore> mpc_;
    std::vector<DelayLine> dly_sp_, dly_mpc_, bypass_;
    std::vector<double> xbuf_, vbuf_, hbuf_, hbuf2_, ybuf_, bbuf_, g2_, g10_, g11_, gtrim_, gbyp_;
    GainRamp ramp_sp_level_, ramp_interstage_, ramp_trim_; Switch sw_sp_step_, sw_mpc_step_, sw_bypass_;
    double g_mpc_record_ = 1.0; std::int64_t host_clock_ = 0, d_sp_ = 0, d_mpc_ = 0, r1_ = 0;
    Meters meters_;
};

}  // namespace smlsp3000
