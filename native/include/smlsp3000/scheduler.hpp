// Exact rational machine clock on the proxy grid (port of smlsp3000/reference/scheduler.py with zero capture/hold
// offsets; the research-only per-channel offsets are not ported and are rejected at prepare()).
#pragma once
#include <cstdint>
#include "smlsp3000/numerics.hpp"

namespace smlsp3000 {

struct RationalClock {
    std::int64_t per_num = 1, per_den = 1;   // proxy samples per machine sample = per_num/per_den (reduced)
    std::int64_t next_k = 0;
    // period = proxy_rate * rate_den / rate_num
    void configure(std::int64_t rate_num, std::int64_t rate_den, std::int64_t proxy_rate) {
        std::int64_t n = proxy_rate * rate_den, d = rate_num;
        const std::int64_t g = num::gcd64(n, d); per_num = n / g; per_den = d / g; next_k = 0;
    }
    void reset() { next_k = 0; }
    // sampling instant of machine sample k: base = floor(k*per), residue = (k*per_num) mod per_den (units 1/per_den)
    void position(std::int64_t k, std::int64_t& base, std::int64_t& residue) const {
        const std::int64_t v = k * per_num; base = num::floor_div(v, per_den); residue = v - base * per_den;
    }
    bool position_le(std::int64_t k, std::int64_t max_pos) const { return k * per_num <= max_pos * per_den; }
    // largest k with hold edge k*per <= t (may be negative before the first sample)
    std::int64_t latest_sample_at(std::int64_t t) const { return num::floor_div(t * per_den, per_num); }
    // hold edge of code e as a correctly rounded double (Fraction.__float__ semantics)
    double hold_position_f(std::int64_t e) const { return static_cast<double>(e * per_num) / static_cast<double>(per_den); }
};

}  // namespace smlsp3000
