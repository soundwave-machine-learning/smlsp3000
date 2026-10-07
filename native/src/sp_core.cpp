#include "smlsp3000/sp_core.hpp"
#include "smlsp3000/numerics.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>

namespace smlsp3000 {

bool SPCore::prepare(const SPCoreConfig& cfg, const TapTable* sampler_taps, const StepTable* step) {
    cfg_ = cfg; taps_ = sampler_taps; step_ = step;
    clock_.configure(cfg.rate_num, cfg.rate_den, cfg.proxy_rate);
    if (taps_->den != clock_.per_den || taps_->half_width != cfg.hw_s || step_->half_width != cfg.hw_z) return false;
    D_ = static_cast<std::int64_t>(cfg.hw_s) + cfg.hw_z;
    code_scale_ = cfg.dac_fs / cfg.full_scale_codes;
    const std::int64_t per_ceil = (clock_.per_num + clock_.per_den - 1) / clock_.per_den;
    hist_.assign(cfg.max_chunk + 2 * static_cast<std::size_t>(cfg.hw_s) + static_cast<std::size_t>(per_ceil) + 16, 0.0);
    const std::int64_t per_floor = std::max<std::int64_t>(1, clock_.per_num / clock_.per_den);
    codes_.assign(static_cast<std::size_t>(cfg.max_chunk / static_cast<std::size_t>(per_floor)) + 2 * static_cast<std::size_t>(cfg.hw_z) + 1024, 0.0);
    reset();
    return true;
}

void SPCore::reset() {
    clock_.reset();
    hist_len_ = static_cast<std::size_t>(cfg_.hw_s);                 // pre-padded zeros: samples before t=0 are zero
    std::fill(hist_.begin(), hist_.begin() + static_cast<std::ptrdiff_t>(hist_len_), 0.0);
    hist_start_ = -static_cast<std::int64_t>(cfg_.hw_s);
    codes_start_ = 0; codes_len_ = 0; n_out_ = 0; clip_count_ = 0; peak_in_ = 0.0;
}

void SPCore::process(const double* v, const double* gain, std::size_t n, double* out) {
    // R2 (analog clamp INACTIVE) / R3 (INACTIVE): append gain * v to the proxy history
    double* h = hist_.data() + hist_len_;
    double pk = peak_in_;
    for (std::size_t i = 0; i < n; ++i) { const double a = std::fabs(v[i]); if (a > pk) pk = a; h[i] = v[i] * gain[i]; }
    peak_in_ = pk; hist_len_ += n;
    const std::int64_t avail_end = hist_start_ + static_cast<std::int64_t>(hist_len_);
    // R4/R5: every machine sample whose interpolation window is available
    const std::int64_t max_pos = avail_end - 1 - cfg_.hw_s;
    const int W = taps_->width;
    while (clock_.position_le(clock_.next_k, max_pos)) {
        const std::int64_t k = clock_.next_k; std::int64_t base, residue; clock_.position(k, base, residue);
        const double* win = hist_.data() + static_cast<std::size_t>(base - cfg_.hw_s + 1 - hist_start_);
        const double s = num::pairwise_dot(win, taps_->row(residue), static_cast<std::size_t>(W));
        double code;
        if (cfg_.quant_bypass) code = s * cfg_.full_scale_codes;
        else {
            const double r = s * cfg_.full_scale_codes + cfg_.offset_codes;
            const double raw = cfg_.rule == 0 ? std::floor(r + 0.5) : std::floor(r);
            code = raw; if (code < cfg_.code_min) code = cfg_.code_min; if (code > cfg_.code_max) code = cfg_.code_max;
            if (raw != code) ++clip_count_;
        }
        if (codes_len_ == 0) codes_start_ = k;
        codes_[codes_len_++] = code;
        if (tap_codes) tap_codes->push(code);
        clock_.next_k = k + 1;
    }
    // R7: band-limited hold for output proxy indices [n_out, avail_end); output n ↔ time t = n - D
    const std::int64_t n0 = n_out_, n1 = avail_end;
    const std::size_t cnt = static_cast<std::size_t>(n1 - n0);
    if (cnt) {
        const std::int64_t t0 = n0 - D_, t1 = n1 - 1 - D_;
        for (std::size_t i = 0; i < cnt; ++i) {
            const std::int64_t kh = clock_.latest_sample_at(t0 + static_cast<std::int64_t>(i));
            out[i] = kh < 0 ? 0.0 : code_at(kh);
        }
        const std::int64_t e_lo = clock_.latest_sample_at(t0 - cfg_.hw_z) + 1, e_hi = clock_.latest_sample_at(t1 + cfg_.hw_z);
        for (std::int64_t e = std::max<std::int64_t>(e_lo, 0); e <= e_hi; ++e) {
            const double pef = clock_.hold_position_f(e);
            const double delta = code_at(e) - (e > 0 ? code_at(e - 1) : 0.0);
            if (delta == 0.0) continue;
            const std::int64_t fl = static_cast<std::int64_t>(std::floor(pef));
            const std::int64_t a = std::max(fl - cfg_.hw_z + 1, t0), b = std::min(fl + cfg_.hw_z, t1);
            for (std::int64_t tt = a; tt <= b; ++tt) {
                const double d = static_cast<double>(tt) - pef;
                const double corr = (*step_)(d) - (d >= 0.0 ? 1.0 : 0.0);
                out[static_cast<std::size_t>(tt - t0)] += delta * corr;
            }
        }
        for (std::size_t i = 0; i < cnt; ++i) out[i] = out[i] * code_scale_;      // R8 identity, then R9 below
        for (std::size_t i = 0; i < cnt; ++i) out[i] = out[i] * cfg_.out_gain;
        n_out_ = n1;
        // prune codes older than needed
        const std::int64_t keep_from_k = clock_.latest_sample_at(t1 - cfg_.hw_z) - 2;
        if (keep_from_k > codes_start_ && codes_len_) {
            const std::int64_t drop = std::min<std::int64_t>(keep_from_k - codes_start_, static_cast<std::int64_t>(codes_len_));
            std::memmove(codes_.data(), codes_.data() + drop, (codes_len_ - static_cast<std::size_t>(drop)) * sizeof(double));
            codes_len_ -= static_cast<std::size_t>(drop); codes_start_ += drop;
            if (codes_len_ == 0) codes_start_ = clock_.next_k;
        }
    }
    // prune proxy history older than needed by the next sampling window
    std::int64_t nb, nr; clock_.position(clock_.next_k, nb, nr);
    const std::int64_t oldest_needed = nb - cfg_.hw_s - 1;
    const std::int64_t drop = oldest_needed - hist_start_;
    if (drop > 0) {
        std::memmove(hist_.data(), hist_.data() + drop, (hist_len_ - static_cast<std::size_t>(drop)) * sizeof(double));
        hist_len_ -= static_cast<std::size_t>(drop); hist_start_ += drop;
    }
}

}  // namespace smlsp3000
