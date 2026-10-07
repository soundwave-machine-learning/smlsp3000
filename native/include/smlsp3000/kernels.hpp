// Kernel tables (IMPLEMENTATION, not machine behaviour) — ports of smlsp3000/reference/kernels.py.
#pragma once
#include <cstdint>
#include <string>
#include <vector>

namespace smlsp3000 {

// |sum(h) - 1| bound after normalisation (4 ulp of 1.0), as in the reference.
inline constexpr double DC_GAIN_BOUND = 4.0 * 2.220446049250313e-16;

// Odd-length windowed-sinc low-pass; cutoff in cycles/sample; DC gain folded to 1 within DC_GAIN_BOUND.
// Returns false (and sets err) if the bound cannot be met.
bool kaiser_sinc_lowpass(int num_taps, double cutoff, double beta, std::vector<double>& h, double& dc_residual, std::string& err);

// Exact interpolation taps for every fractional position r/den (TapTable in the reference).
struct TapTable {
    int half_width = 0; double beta = 0.0; std::int64_t den = 1; int width = 0;   // width = 2*half_width
    std::vector<double> table;                                                     // den * width
    static constexpr std::int64_t MAX_DEN = 1 << 16;
    bool build(int hw, double b, std::int64_t d, std::string& err);
    const double* row(std::int64_t residue) const { return table.data() + static_cast<std::size_t>(residue) * static_cast<std::size_t>(width); }
};

// Band-limited unit step S(d) table (BandlimitedStepTable in the reference): resolution 1/res, |d| <= half_width.
struct StepTable {
    int half_width = 0; double beta = 0.0; int res = 1024; double truncation_residual = 0.0;
    std::vector<double> table;
    void build(int hw, double b);
    double operator()(double d) const;
};

// Design-derived kernel properties (same formulas as PreparedInfo.kernel_properties in the reference).
struct KernelProperties {
    double lowpass_design_attenuation_db = 0.0, lowpass_transition_width_hz = 0.0, interp_design_attenuation_db = 0.0;
};

}  // namespace smlsp3000
