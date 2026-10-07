// SP-1200 core R2–R9 on the proxy grid, one channel (port of SPReferenceEngine.core_channel, sp1200-reference-impl-1.0.4).
#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>
#include "smlsp3000/kernels.hpp"
#include "smlsp3000/scheduler.hpp"

namespace smlsp3000 {

struct TapSink {   // offline diagnostics only (preallocated by the tool; never used in release processing)
    double* data = nullptr; std::size_t cap = 0, count = 0, dropped = 0;
    void push(double v) { if (count < cap) data[count++] = v; else ++dropped; }
};

struct SPCoreConfig {
    std::int64_t rate_num = 0, rate_den = 1, proxy_rate = 0;
    double full_scale_codes = 0.0, code_min = 0.0, code_max = 0.0, offset_codes = 0.0, dac_fs = 1.0, out_gain = 1.0;
    int rule = 0;                 // 0 ROUND_NEAREST (⌊r+½⌋), 1 FLOOR (⌊r⌋)
    bool quant_bypass = false;
    int hw_s = 0, hw_z = 0;       // proxy samples
    std::size_t max_chunk = 0;    // proxy samples per call
};

class SPCore {
public:
    bool prepare(const SPCoreConfig& cfg, const TapTable* sampler_taps, const StepTable* step);
    void reset();
    // v: proxy input (len n), gain: per-sample R2 gain (len n), out: proxy output (len n), delayed by core_delay()
    void process(const double* v, const double* gain, std::size_t n, double* out);
    std::int64_t core_delay() const { return D_; }
    std::int64_t clip_count() const { return clip_count_; }
    double peak_core_input() const { return peak_in_; }
    void reset_meters() { clip_count_ = 0; peak_in_ = 0.0; }
    TapSink* tap_codes = nullptr;
    const RationalClock& clock() const { return clock_; }
private:
    double code_at(std::int64_t k) const { return k < codes_start_ ? 0.0 : codes_[static_cast<std::size_t>(k - codes_start_)]; }
    SPCoreConfig cfg_; const TapTable* taps_ = nullptr; const StepTable* step_ = nullptr; RationalClock clock_;
    std::vector<double> hist_; std::int64_t hist_start_ = 0; std::size_t hist_len_ = 0;
    std::vector<double> codes_; std::int64_t codes_start_ = 0; std::size_t codes_len_ = 0;
    std::int64_t n_out_ = 0, D_ = 0, clip_count_ = 0; double peak_in_ = 0.0, code_scale_ = 0.0;
};

}  // namespace smlsp3000
