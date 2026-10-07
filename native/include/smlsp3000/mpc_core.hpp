// MPC3000 core R11–R15 on the proxy grid, one channel (port of MPCReferenceEngine.core_channel, mpc3000-reference-impl-1.0.2).
#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>
#include "smlsp3000/kernels.hpp"
#include "smlsp3000/scheduler.hpp"
#include "smlsp3000/sp_core.hpp"
#include "smlsp3000/streaming.hpp"

namespace smlsp3000 {

struct MPCCoreConfig {
    std::int64_t rate_num = 0, rate_den = 1, proxy_rate = 0;
    double c18_fs = 0.0, c18_min = 0.0, c18_max = 0.0, c16_min = 0.0, c16_max = 0.0, expand = 4.0, dac_fs = 1.0;
    int rule = 0;                 // 0 ROUND_NEAREST (⌊c18/4+½⌋), 1 TRUNCATION (⌊c18/4⌋)
    bool quant_bypass = false;
    int hw_s = 0, hw_r = 0;       // hw_s proxy samples, hw_r machine samples
    int L = 1; std::size_t max_chunk = 0;
    bool exact_reference_order = false;   // true: evaluate R12 FIR → sampler and R15 → R16 as separate stages in the reference's arithmetic order
};

class MPCCore {
public:
    bool prepare(const MPCCoreConfig& cfg, const std::vector<double>& h_r12, const std::vector<double>& h_lp, const TapTable* sampler_taps, const TapTable* recon_taps);
    void reset();
    void process(const double* v, const double* gain, std::size_t n, double* out);                 // proxy-grid output (R15 reconstruction)
    void process_to_host(const double* v, const double* gain, std::size_t n, double* y_host);     // composed R15+R16: host-rate output, n % L == 0
    bool composed() const { return !cfg_.exact_reference_order; }
    std::int64_t core_delay() const { return r12_half_ + D15_; }
    std::int64_t D15() const { return D15_; }
    std::int64_t clip18_count() const { return clip18_; }
    std::int64_t clamp16_count() const { return clip16_; }
    double peak_core_input() const { return peak_in_; }
    void reset_meters() { clip18_ = 0; clip16_ = 0; peak_in_ = 0.0; }
    TapSink* tap_c18 = nullptr; TapSink* tap_c16 = nullptr;
    const RationalClock& clock() const { return clock_; }
private:
    void ingest(const double* v, const double* gain, std::size_t n);     // R11, R12 (band limitation + sampling), R13, R14 store
    void build_composed_tables(const std::vector<double>& h_r12, const std::vector<double>& h_lp);
    MPCCoreConfig cfg_; StreamingFIR bandlimit_; Decimator decim_;
    // composed operator tables (IMPLEMENTATION): sampler ∘ band-limit per residue; (R16 decimator ∘ reconstruction) per host phase class
    std::vector<double> comb_samp_; int comb_samp_w_ = 0; std::int64_t comb_hist_extra_ = 0;
    std::vector<double> comb_out_; int comb_out_w_ = 0; std::int64_t comb_out_s0_ = 0, comb_classes_ = 0, comb_base_ = 0;
    std::vector<double> y_proxy_scratch_; const TapTable* staps_ = nullptr; const TapTable* rtaps_ = nullptr; RationalClock clock_;
    std::vector<double> scratch_, hist_, d18_;            // d18_[k - d18_start_] = expand * c16[k]; zeros for k < 0
    std::int64_t hist_start_ = 0, d18_start_ = 0, n_out_ = 0, r12_half_ = 0, D15_ = 0, clip18_ = 0, clip16_ = 0;
    std::size_t hist_len_ = 0, d18_len_ = 0; double peak_in_ = 0.0, out_scale_ = 0.0;
};

}  // namespace smlsp3000
