// Block-streaming FIR primitives with exact partition invariance (port of smlsp3000/reference/streaming.py).
// Each output sample is the numpy-ordered pairwise dot of its own tap window; the state is the last len(h)-1
// inputs. All buffers are preallocated in prepare(); process() never allocates.
#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>

namespace smlsp3000 {

class StreamingFIR {   // y[n] = sum_k h[k] x[n-k]
public:
    void prepare(const std::vector<double>& h, std::size_t max_chunk);
    void reset();
    void process(const double* x, std::size_t n, double* y);     // n <= max_chunk
    std::size_t taps() const { return M_; }
private:
    std::vector<double> taps_rev_, buf_; std::size_t M_ = 0, max_chunk_ = 0;
};

class PolyphaseUpsampler {   // y[n*L+p] = sum_k hp[k] x[n-k], hp[k] = L*h[k*L+p]
public:
    void prepare(int L, const std::vector<double>& h, std::size_t max_chunk);
    void reset();
    void process(const double* x, std::size_t n, double* y);     // y has n*L samples
    int L() const { return L_; }
private:
    int L_ = 1; std::size_t n_per_phase_ = 0, max_chunk_ = 0;
    std::vector<double> phase_taps_rev_, buf_;
};

class Decimator {   // low-pass h then keep every L-th sample (phase 0); input length multiple of L
public:
    void prepare(int L, const std::vector<double>& h, std::size_t max_chunk_in);
    void reset();
    void process(const double* v, std::size_t n, double* y);     // n <= max_chunk_in, n % L == 0; y has n/L
private:
    int L_ = 1; std::size_t M_ = 0, max_chunk_ = 0; std::vector<double> taps_rev_, buf_;
};

class DelayLine {   // exact integer delay with zero initial state
public:
    void prepare(std::size_t n, std::size_t max_chunk);
    void reset();
    void process(const double* x, std::size_t n, double* y);     // in-place allowed when x == y
    std::size_t delay() const { return n_; }
private:
    std::size_t n_ = 0, max_chunk_ = 0; std::vector<double> buf_;
};

}  // namespace smlsp3000
