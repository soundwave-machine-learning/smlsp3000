#include "smlsp3000/streaming.hpp"
#include "smlsp3000/numerics.hpp"
#include <algorithm>
#include <cstring>

namespace smlsp3000 {

void StreamingFIR::prepare(const std::vector<double>& h, std::size_t max_chunk) {
    M_ = h.size(); max_chunk_ = max_chunk;
    taps_rev_.assign(h.rbegin(), h.rend());
    buf_.assign(M_ - 1 + max_chunk_, 0.0);
    reset();
}
void StreamingFIR::reset() { std::fill(buf_.begin(), buf_.begin() + static_cast<std::ptrdiff_t>(M_ - 1), 0.0); }
void StreamingFIR::process(const double* x, std::size_t n, double* y) {
    double* b = buf_.data();
    std::memcpy(b + (M_ - 1), x, n * sizeof(double));            // buf = [state | x]
    for (std::size_t i = 0; i < n; ++i) y[i] = num::pairwise_dot(b + i, taps_rev_.data(), M_);
    if (M_ > 1) std::memmove(b, b + n, (M_ - 1) * sizeof(double));   // state = last M-1 of buf
}

void PolyphaseUpsampler::prepare(int L, const std::vector<double>& h, std::size_t max_chunk) {
    L_ = L; max_chunk_ = max_chunk;
    n_per_phase_ = (h.size() + static_cast<std::size_t>(L) - 1) / static_cast<std::size_t>(L);
    phase_taps_rev_.assign(static_cast<std::size_t>(L) * n_per_phase_, 0.0);
    const double Ld = static_cast<double>(L);
    for (int p = 0; p < L; ++p) {
        std::vector<double> taps;                                 // numpy: h[p::L] * L, zero-padded to n_per_phase, then reversed
        for (std::size_t k = static_cast<std::size_t>(p); k < h.size(); k += static_cast<std::size_t>(L)) taps.push_back(h[k] * Ld);
        taps.resize(n_per_phase_, 0.0);
        double* row = phase_taps_rev_.data() + static_cast<std::size_t>(p) * n_per_phase_;
        for (std::size_t j = 0; j < n_per_phase_; ++j) row[j] = taps[n_per_phase_ - 1 - j];
    }
    buf_.assign(n_per_phase_ - 1 + max_chunk_, 0.0);
    reset();
}
void PolyphaseUpsampler::reset() { std::fill(buf_.begin(), buf_.begin() + static_cast<std::ptrdiff_t>(n_per_phase_ - 1), 0.0); }
void PolyphaseUpsampler::process(const double* x, std::size_t n, double* y) {
    double* b = buf_.data();
    std::memcpy(b + (n_per_phase_ - 1), x, n * sizeof(double));
    for (int p = 0; p < L_; ++p) {
        const double* row = phase_taps_rev_.data() + static_cast<std::size_t>(p) * n_per_phase_;
        for (std::size_t i = 0; i < n; ++i) y[i * static_cast<std::size_t>(L_) + static_cast<std::size_t>(p)] = num::pairwise_dot(b + i, row, n_per_phase_);
    }
    if (n_per_phase_ > 1) std::memmove(b, b + n, (n_per_phase_ - 1) * sizeof(double));
}

void Decimator::prepare(int L, const std::vector<double>& h, std::size_t max_chunk_in) {
    L_ = L; M_ = h.size(); max_chunk_ = max_chunk_in;
    taps_rev_.assign(h.rbegin(), h.rend());
    buf_.assign(M_ - 1 + max_chunk_, 0.0);
    reset();
}
void Decimator::reset() { std::fill(buf_.begin(), buf_.begin() + static_cast<std::ptrdiff_t>(M_ - 1), 0.0); }
void Decimator::process(const double* v, std::size_t n, double* y) {
    double* b = buf_.data();
    std::memcpy(b + (M_ - 1), v, n * sizeof(double));
    const std::size_t count = n / static_cast<std::size_t>(L_);
    for (std::size_t i = 0; i < count; ++i) y[i] = num::pairwise_dot(b + i * static_cast<std::size_t>(L_), taps_rev_.data(), M_);
    if (M_ > 1) std::memmove(b, b + n, (M_ - 1) * sizeof(double));
}

void DelayLine::prepare(std::size_t n, std::size_t max_chunk) { n_ = n; max_chunk_ = max_chunk; buf_.assign(n_ + max_chunk_, 0.0); reset(); }
void DelayLine::reset() { std::fill(buf_.begin(), buf_.begin() + static_cast<std::ptrdiff_t>(n_), 0.0); }
void DelayLine::process(const double* x, std::size_t n, double* y) {
    if (n_ == 0) { if (x != y) std::memmove(y, x, n * sizeof(double)); return; }
    double* b = buf_.data();
    std::memcpy(b + n_, x, n * sizeof(double));                   // full = [buf | x]
    std::memmove(y, b, n * sizeof(double));                       // y = full[:n]
    std::memmove(b, b + n, n_ * sizeof(double));                  // buf = full[-n:]
}

}  // namespace smlsp3000
