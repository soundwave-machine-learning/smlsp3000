#include "smlsp3000/kernels.hpp"
#include "smlsp3000/numerics.hpp"
#include <cmath>

namespace smlsp3000 {

bool kaiser_sinc_lowpass(int num_taps, double cutoff, double beta, std::vector<double>& h, double& dc_residual, std::string& err) {
    if (num_taps % 2 == 0 || num_taps < 1) { err = "num_taps must be odd"; return false; }
    const int m = (num_taps - 1) / 2;
    h.assign(static_cast<std::size_t>(num_taps), 0.0);
    const double two_cutoff = 2.0 * cutoff;                       // numpy: (2.0 * cutoff) is a scalar product first
    const double hw = static_cast<double>(m + 1);
    for (int i = 0; i < num_taps; ++i) {
        const double n = static_cast<double>(i - m);
        h[static_cast<std::size_t>(i)] = two_cutoff * num::exact_sinc(two_cutoff * n) * num::kaiser_window(n, hw, beta);
    }
    const double s = num::pairwise_sum(h.data(), h.size());
    for (auto& v : h) v = v / s;
    for (int pass = 0; pass < 2; ++pass) h[static_cast<std::size_t>(m)] -= (num::pairwise_sum(h.data(), h.size()) - 1.0);
    dc_residual = std::fabs(num::pairwise_sum(h.data(), h.size()) - 1.0);
    if (dc_residual > DC_GAIN_BOUND) { err = "low-pass DC gain not within float64 bound"; return false; }
    return true;
}

bool TapTable::build(int hw, double b, std::int64_t d, std::string& err) {
    if (d < 1 || d > MAX_DEN) { err = "tap table denominator outside the supported range (direct evaluation not ported)"; return false; }
    half_width = hw; beta = b; den = d; width = 2 * hw;
    table.assign(static_cast<std::size_t>(den) * static_cast<std::size_t>(width), 0.0);
    const double hwd = static_cast<double>(hw);
    for (std::int64_t r = 0; r < den; ++r) {
        const double frac = static_cast<double>(r) / static_cast<double>(den);
        double* row = table.data() + static_cast<std::size_t>(r) * static_cast<std::size_t>(width);
        for (int j = 0; j < width; ++j) {
            const double k = static_cast<double>(-hw + 1 + j);
            const double dd = k - frac;
            row[j] = num::exact_sinc(dd) * num::kaiser_window(dd, hwd, beta);
        }
    }
    return true;
}

void StepTable::build(int hw, double b) {
    half_width = hw; beta = b;
    const std::int64_t n = static_cast<std::int64_t>(2) * hw * res + 1;
    std::vector<double> w(static_cast<std::size_t>(n));
    const double hwd = static_cast<double>(hw);
    for (std::int64_t i = 0; i < n; ++i) {
        const double x = static_cast<double>(-static_cast<std::int64_t>(hw) * res + i) / static_cast<double>(res);
        w[static_cast<std::size_t>(i)] = num::exact_sinc(x) * num::kaiser_window(x, hwd, beta);
    }
    table.assign(static_cast<std::size_t>(n), 0.0);
    double cum = 0.0;                                             // np.cumsum: sequential
    for (std::int64_t i = 1; i < n; ++i) {
        cum += 0.5 * (w[static_cast<std::size_t>(i)] + w[static_cast<std::size_t>(i - 1)]) / static_cast<double>(res);
        table[static_cast<std::size_t>(i)] = cum;
    }
    truncation_residual = std::fabs(cum - 1.0);
    for (auto& v : table) v = v / cum;
}

double StepTable::operator()(double d) const {
    const double hw = static_cast<double>(half_width);
    if (d >= hw) return 1.0;
    if (!(d > -hw)) return 0.0;                                   // d <= -hw (and NaN → 0 as np.where would not; inputs are finite)
    const double pos = (d - (-hw)) * static_cast<double>(res);
    std::int64_t i = static_cast<std::int64_t>(std::floor(pos));
    const double f = pos - static_cast<double>(i);
    const std::int64_t last = static_cast<std::int64_t>(table.size()) - 2;
    if (i < 0) i = 0; if (i > last) i = last;
    return table[static_cast<std::size_t>(i)] * (1.0 - f) + table[static_cast<std::size_t>(i + 1)] * f;
}

}  // namespace smlsp3000
