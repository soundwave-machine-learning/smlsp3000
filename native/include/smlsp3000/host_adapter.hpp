// Framework-independent host adapter (Sprint 7, OWN-DEC-029..032, 035): the only object a plugin wrapper talks to.
//  * stereo float32/float64 planar buffers of any length (internal chunking; preallocated conversion buffers)
//  * block-boundary parameter delivery: targets set from any thread (atomics) become native events at offset 0 of the next block
//  * lock-free state handoff: a validated ProductParameters record is published to the audio thread (double buffer, atomic index)
//  * plugin bypass: latency-aligned ORIGINAL input (before every product gain and both machines) with a 10 ms linear crossfade,
//    complementary weights, continuing from the current position on rapid toggles; the core keeps running while bypassed
//  * meters: atomics written by the audio thread (peaks per block, cumulative clamp counts, fault/over-range flags)
// No allocation, lock, I/O or logging in process(). The DSP is the unchanged Sprint 6 core.
#pragma once
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include "smlsp3000/engine.hpp"

namespace smlsp3000 {

inline constexpr int ADAPTER_CHANNELS = 2;
inline constexpr double BYPASS_CROSSFADE_MS = 10.0;
inline constexpr const char* HOST_ADAPTER_VERSION = "smlsp3000-host-adapter-1.0.0";

struct MeterSnapshot {
    double input_peak[2]{}, mpc_core_input_peak[2]{}, output_peak[2]{};     // per-block peaks of the last processed block
    double input_peak_hold[2]{}, output_peak_hold[2]{};                     // max since the last reset_hold()
    std::int64_t sp_clip[2]{}, mpc_clip18[2]{}, mpc_clamp16[2]{};           // cumulative since reset()
    std::int64_t nonfinite_input_samples = 0, faults = 0, events_rejected = 0, blocks_processed = 0;
    bool fault_latched = false, output_over_range[2]{};                     // |out| > 1.0 (finite) in the last block — indication only, never clamped
    double bypass_weight = 1.0;                                             // 1 = fully processed, 0 = fully bypassed
    bool prepared = false; std::int64_t latency = 0; int host_rate = 0;
};

class HostAdapter {
public:
    PrepareResult prepare(int host_rate, std::size_t max_block, const ProductParameters& initial, const ResearchConfiguration* research = nullptr);
    bool prepared() const { return prepared_; }
    void reset();                                                 // stream start: core reset, dry delay cleared, crossfade snapped to its target, meters cleared
    std::int64_t latency() const { return prepared_ ? engine_.latency() : 0; }
    const Engine& engine() const { return engine_; }
    // ---- parameters (any thread; applied at the next block boundary)
    void set_parameter(ParamId id, double value);                 // dB value / step dB / enum index / 0|1
    double parameter(ParamId id) const { return targets_[static_cast<int>(id)].load(std::memory_order_relaxed); }
    static double clamp_parameter(ParamId id, double value);      // documented range policy for host values
    // ---- state (message thread only; nothing here touches the audio thread except the final atomic publish)
    StateLoadResult load_state(std::string_view native_state_text);   // validates, sets targets, publishes to the audio thread
    std::string save_state() const;                                   // native schema v1 text from the current targets
    // ---- audio (audio thread)
    void process(const double* const* in, double* const* out, std::size_t frames);
    void process(const float* const* in, float* const* out, std::size_t frames);
    // ---- meters (any thread)
    MeterSnapshot meters() const;
    void reset_hold();
    // ---- introspection
    static constexpr int parameter_count() { return 6; }
private:
    void apply_pending_and_events();
    void process_chunk(const double* const* in, double* const* out, std::size_t n);
    Engine engine_; bool prepared_ = false; int host_rate_ = 0; std::size_t max_block_ = 0;
    std::array<std::atomic<double>, 6> targets_{}; std::array<double, 6> applied_{};
    // state handoff: two slots; writer fills the inactive slot then publishes its index; reader consumes once
    std::array<ProductParameters, 2> slots_; std::atomic<int> pending_slot_{-1}; int writer_slot_ = 0;
    std::vector<DelayLine> dry_; std::vector<double> dbuf_, sbuf_[2], in64_[2], out64_[2]; std::vector<double*> outp_; std::vector<const double*> inp_;
    double w_ = 1.0, w_step_ = 0.0;
    // meters (atomics)
    std::array<std::atomic<double>, 2> m_in_{}, m_mpc_{}, m_out_{}, m_in_hold_{}, m_out_hold_{}; std::array<std::atomic<std::int64_t>, 2> m_sp_clip_{}, m_c18_{}, m_c16_{};
    std::atomic<std::int64_t> m_nonfinite_{0}, m_faults_{0}, m_rejected_{0}, m_blocks_{0}; std::atomic<bool> m_fault_{false}; std::array<std::atomic<bool>, 2> m_over_{}; std::atomic<double> m_w_{1.0};
};

}  // namespace smlsp3000
