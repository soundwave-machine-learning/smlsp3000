#include "smlsp3000/mpc_core.hpp"
#include "smlsp3000/numerics.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>

namespace smlsp3000 {

bool MPCCore::prepare(const MPCCoreConfig& cfg, const std::vector<double>& h_r12, const std::vector<double>& h_lp, const TapTable* sampler_taps, const TapTable* recon_taps) {
    cfg_ = cfg; staps_ = sampler_taps; rtaps_ = recon_taps;
    clock_.configure(cfg.rate_num, cfg.rate_den, cfg.proxy_rate);          // P = per_num/per_den
    if (staps_->den != clock_.per_den || rtaps_->den != clock_.per_num || staps_->half_width != cfg.hw_s || rtaps_->half_width != cfg.hw_r) return false;
    r12_half_ = static_cast<std::int64_t>((h_r12.size() - 1) / 2);
    // D15 = L * ceil((hw_r*P + hw_s)/L)
    const std::int64_t la_num = static_cast<std::int64_t>(cfg.hw_r) * clock_.per_num + static_cast<std::int64_t>(cfg.hw_s) * clock_.per_den;
    const std::int64_t la_den = clock_.per_den * cfg.L;
    D15_ = static_cast<std::int64_t>(cfg.L) * ((la_num + la_den - 1) / la_den);
    out_scale_ = cfg.dac_fs / cfg.c18_fs;
    bandlimit_.prepare(h_r12, cfg.max_chunk); decim_.prepare(cfg.L, h_lp, cfg.max_chunk);
    scratch_.assign(cfg.max_chunk, 0.0); y_proxy_scratch_.assign(cfg.max_chunk, 0.0);
    comb_hist_extra_ = cfg.exact_reference_order ? 0 : 2 * r12_half_;
    if (!cfg.exact_reference_order) build_composed_tables(h_r12, h_lp);
    const std::int64_t per_ceil = (clock_.per_num + clock_.per_den - 1) / clock_.per_den;
    hist_.assign(cfg.max_chunk + 2 * static_cast<std::size_t>(cfg.hw_s) + static_cast<std::size_t>(comb_hist_extra_) + static_cast<std::size_t>(per_ceil) + 16, 0.0);
    const std::int64_t per_floor = std::max<std::int64_t>(1, clock_.per_num / clock_.per_den);
    d18_.assign(cfg.max_chunk / static_cast<std::size_t>(per_floor) + 6 * static_cast<std::size_t>(cfg.hw_r) + static_cast<std::size_t>(h_lp.size() / static_cast<std::size_t>(per_floor)) + 2048, 0.0);
    reset();
    return true;
}

void MPCCore::reset() {
    clock_.reset(); bandlimit_.reset(); decim_.reset();
    hist_len_ = static_cast<std::size_t>(cfg_.hw_s + comb_hist_extra_);          // zeros before t = 0 (and the implicit zero FIR state in composed mode)
    std::fill(hist_.begin(), hist_.begin() + static_cast<std::ptrdiff_t>(hist_len_), 0.0);
    hist_start_ = -static_cast<std::int64_t>(cfg_.hw_s + comb_hist_extra_);
    // zeros for codes before stream start: the first reconstruction windows reach k >= kc(-D15) - hw_r + 1 (proxy output) and
    // k >= kc(-D15) + comb_out_s0_ (composed host output); pad generously from those exact first-window indices
    const std::int64_t kb_first = num::floor_div(-D15_ * clock_.per_den, clock_.per_num);
    const std::int64_t need_proxy = -(kb_first - cfg_.hw_r + 1), need_comb = cfg_.exact_reference_order ? 0 : -(kb_first + comb_out_s0_);
    d18_start_ = -(std::max(need_proxy, need_comb) + 64);
    d18_len_ = static_cast<std::size_t>(-d18_start_);
    std::fill(d18_.begin(), d18_.begin() + static_cast<std::ptrdiff_t>(d18_len_), 0.0);
    n_out_ = 0; clip18_ = 0; clip16_ = 0; peak_in_ = 0.0;
}

void MPCCore::ingest(const double* v, const double* gain, std::size_t n) {
    double pk = peak_in_;
    for (std::size_t i = 0; i < n; ++i) { const double a = std::fabs(v[i]); if (a > pk) pk = a; scratch_[i] = v[i] * gain[i]; }   // R11
    peak_in_ = pk;
    if (cfg_.exact_reference_order) bandlimit_.process(scratch_.data(), n, hist_.data() + hist_len_);   // R12 TRANSPARENT band limitation as a separate stage
    else std::memcpy(hist_.data() + hist_len_, scratch_.data(), n * sizeof(double));                   // composed: band limitation folded into the sampler taps
    hist_len_ += n;
    const std::int64_t avail_end = hist_start_ + static_cast<std::int64_t>(hist_len_);
    const std::int64_t max_pos = avail_end - 1 - cfg_.hw_s;
    const int W = cfg_.exact_reference_order ? staps_->width : comb_samp_w_;
    const std::int64_t back = cfg_.hw_s - 1 + comb_hist_extra_;
    while (clock_.position_le(clock_.next_k, max_pos)) {                   // R12 sampling → 18-bit code → R13 → store (R14 identity)
        const std::int64_t k = clock_.next_k; std::int64_t base, residue; clock_.position(k, base, residue);
        const double* win = hist_.data() + static_cast<std::size_t>(base - back - hist_start_);
        const double* row = cfg_.exact_reference_order ? staps_->row(residue) : comb_samp_.data() + static_cast<std::size_t>(residue) * static_cast<std::size_t>(comb_samp_w_);
        const double s = num::pairwise_dot(win, row, static_cast<std::size_t>(W));
        double c16;
        if (cfg_.quant_bypass) c16 = s * (cfg_.c18_fs / cfg_.expand);
        else {
            const double raw18 = std::floor(s * cfg_.c18_fs + 0.5);
            double c18 = raw18; if (c18 < cfg_.c18_min) c18 = cfg_.c18_min; if (c18 > cfg_.c18_max) c18 = cfg_.c18_max;
            if (raw18 != c18) ++clip18_;
            const double raw16 = cfg_.rule == 0 ? std::floor(c18 / 4.0 + 0.5) : std::floor(c18 / 4.0);
            c16 = raw16; if (c16 < cfg_.c16_min) c16 = cfg_.c16_min; if (c16 > cfg_.c16_max) c16 = cfg_.c16_max;
            if (raw16 != c16) ++clip16_;
            if (tap_c18) tap_c18->push(c18);
        }
        if (tap_c16) tap_c16->push(c16);
        d18_[d18_len_++] = c16 * cfg_.expand;                                // exact x4 re-expansion (R14/R15 unity)
        clock_.next_k = k + 1;
    }
}

void MPCCore::process(const double* v, const double* gain, std::size_t n, double* out) {
    ingest(v, gain, n);
    const std::int64_t avail_end = hist_start_ + static_cast<std::int64_t>(hist_len_);
    // R15 TRANSPARENT reconstruction for output proxy indices [n_out, avail_end); output n ↔ time n - D15
    const std::int64_t n0 = n_out_, n1 = avail_end; const int WR = rtaps_->width;
    for (std::int64_t nn = n0; nn < n1; ++nn) {
        const std::int64_t tq = nn - D15_;
        const std::int64_t u_num = tq * clock_.per_den, u_den = clock_.per_num;
        const std::int64_t kc = num::floor_div(u_num, u_den), residue = u_num - kc * u_den;
        const double* win = d18_.data() + static_cast<std::size_t>(kc - cfg_.hw_r + 1 - d18_start_);
        out[static_cast<std::size_t>(nn - n0)] = num::pairwise_dot(win, rtaps_->row(residue), static_cast<std::size_t>(WR)) * out_scale_;
    }
    n_out_ = n1;
    if (n1 > n0) {   // prune codes
        const std::int64_t keep_k = num::floor_div((n1 - 1 - D15_) * clock_.per_den, clock_.per_num) - cfg_.hw_r - 2;
        const std::int64_t drop = keep_k - d18_start_;
        if (drop > 0 && static_cast<std::size_t>(drop) < d18_len_) {
            std::memmove(d18_.data(), d18_.data() + drop, (d18_len_ - static_cast<std::size_t>(drop)) * sizeof(double));
            d18_len_ -= static_cast<std::size_t>(drop); d18_start_ += drop;
        }
    }
    std::int64_t nb, nr; clock_.position(clock_.next_k, nb, nr);
    const std::int64_t oldest_needed = nb - cfg_.hw_s - 1 - comb_hist_extra_;
    const std::int64_t drop = oldest_needed - hist_start_;
    if (drop > 0) {
        std::memmove(hist_.data(), hist_.data() + drop, (hist_len_ - static_cast<std::size_t>(drop)) * sizeof(double));
        hist_len_ -= static_cast<std::size_t>(drop); hist_start_ += drop;
    }
}

void MPCCore::process_to_host(const double* v, const double* gain, std::size_t n, double* y_host) {
    if (cfg_.exact_reference_order) { process(v, gain, n, y_proxy_scratch_.data()); decim_.process(y_proxy_scratch_.data(), n, y_host); return; }
    ingest(v, gain, n);
    const std::int64_t avail_end = hist_start_ + static_cast<std::int64_t>(hist_len_);
    const std::int64_t n0 = n_out_, n1 = avail_end;                         // proxy output indices covered by this call (multiple of L)
    const std::int64_t L = cfg_.L;
    // host output m ↔ proxy index m*L; y[m] = scale * sum_k Wclass[k - kb] * d18[k], kb = floor((m*L - D15)/P)
    for (std::int64_t nn = n0; nn < n1; nn += L) {
        const std::int64_t m = nn / L, tq0 = nn - D15_;
        const std::int64_t kb = num::floor_div(tq0 * clock_.per_den, clock_.per_num);
        const std::int64_t cls = m % comb_classes_;                           // phase class of host output m (period per_num/gcd(L, per_num) host samples)
        const double* row = comb_out_.data() + static_cast<std::size_t>(cls) * static_cast<std::size_t>(comb_out_w_);
        const double* win = d18_.data() + static_cast<std::size_t>(kb + comb_out_s0_ - d18_start_);
        y_host[static_cast<std::size_t>(m - n0 / L)] = num::pairwise_dot(win, row, static_cast<std::size_t>(comb_out_w_)) * out_scale_;
    }
    n_out_ = n1;
    if (n1 > n0) {
        const std::int64_t keep_k = num::floor_div((n1 - L - D15_) * clock_.per_den, clock_.per_num) + comb_out_s0_ - 2;
        const std::int64_t drop = keep_k - d18_start_;
        if (drop > 0 && static_cast<std::size_t>(drop) < d18_len_) {
            std::memmove(d18_.data(), d18_.data() + drop, (d18_len_ - static_cast<std::size_t>(drop)) * sizeof(double));
            d18_len_ -= static_cast<std::size_t>(drop); d18_start_ += drop;
        }
    }
    std::int64_t nb, nr; clock_.position(clock_.next_k, nb, nr);
    const std::int64_t oldest_needed = nb - cfg_.hw_s - 1 - comb_hist_extra_;
    const std::int64_t drop = oldest_needed - hist_start_;
    if (drop > 0) {
        std::memmove(hist_.data(), hist_.data() + drop, (hist_len_ - static_cast<std::size_t>(drop)) * sizeof(double));
        hist_len_ -= static_cast<std::size_t>(drop); hist_start_ += drop;
    }
}

// Composed operator tables. (a) sampler ∘ band limitation: s_k = sum_j T_r[j] * w[base + kk_j], w[n] = sum_m h12[m] v[n - m]
//     => s_k = sum_i C_r[i] * v[base - (hw_s - 1 + 2H) + i], C_r[i] = sum_{j - m' = i - (2H + hw_s - 1) ...} (built by direct convolution).
// (b) R16 decimation ∘ reconstruction: y[m] = sum_q h_lp[q] * u[mL - q], u[n] = scale * sum_i T_{r(n)}[i] * d18[kc(n) + kk_i]
//     => y[m] = scale * sum_k W_cls[k - kb] * d18[k]; the pattern of (kc, r) over q repeats with the class period per_num/gcd(L, per_num).
void MPCCore::build_composed_tables(const std::vector<double>& h_r12, const std::vector<double>& h_lp) {
    const int hw = cfg_.hw_s, Ws = staps_->width; const std::int64_t H = r12_half_, M12 = static_cast<std::int64_t>(h_r12.size());
    comb_samp_w_ = static_cast<int>(Ws + 2 * H);
    comb_samp_.assign(static_cast<std::size_t>(staps_->den) * static_cast<std::size_t>(comb_samp_w_), 0.0);
    // window index i covers v[base - hw + 1 - 2H + i], i in [0, Ws + 2H). Sample tap j sits at w[base + kk_j], kk_j = -hw+1+j; w[n] = sum_m h12[m] v[n-m].
    // contribution of v at offset o = kk_j - m (relative to base): i = o + hw - 1 + 2H = j - m + 2H.
    for (std::int64_t r = 0; r < staps_->den; ++r) {
        double* row = comb_samp_.data() + static_cast<std::size_t>(r) * static_cast<std::size_t>(comb_samp_w_);
        const double* T = staps_->row(r);
        for (int j = 0; j < Ws; ++j) for (std::int64_t m = 0; m < M12; ++m) row[static_cast<std::size_t>(j - m + 2 * H)] += T[j] * h_r12[static_cast<std::size_t>(m)];
    }
    // (b)
    const std::int64_t L = cfg_.L, per_num = clock_.per_num, per_den = clock_.per_den, M = static_cast<std::int64_t>(h_lp.size());
    const std::int64_t n_cls = per_num / num::gcd64(L, per_num);            // host output m and m + n_cls share the same (kc, residue) pattern
    comb_classes_ = n_cls; comb_base_ = 0;
    // code window relative to kb = kc(tq0): k from kc(tq0 - (M-1)) - hw_r + 1 to kb + hw_r; worst case over classes (tq0 = c*L - D15 as in the stream)
    std::int64_t s0 = 0;
    for (std::int64_t c = 0; c < n_cls; ++c) { const std::int64_t tq0 = c * L - D15_; const std::int64_t kb = num::floor_div(tq0 * per_den, per_num); const std::int64_t kmin = num::floor_div((tq0 - (M - 1)) * per_den, per_num) - cfg_.hw_r + 1; s0 = std::min(s0, kmin - kb); }
    comb_out_s0_ = s0; comb_out_w_ = static_cast<int>(cfg_.hw_r - s0 + 1);
    comb_out_.assign(static_cast<std::size_t>(n_cls) * static_cast<std::size_t>(comb_out_w_), 0.0);
    const int WR = rtaps_->width;
    for (std::int64_t c = 0; c < n_cls; ++c) {
        const std::int64_t tq0 = c * L - D15_; const std::int64_t kb = num::floor_div(tq0 * per_den, per_num);
        double* row = comb_out_.data() + static_cast<std::size_t>(c) * static_cast<std::size_t>(comb_out_w_);
        for (std::int64_t q = 0; q < M; ++q) {
            const std::int64_t tq = tq0 - q, u_num = tq * per_den, kc = num::floor_div(u_num, per_num), residue = u_num - kc * per_num;
            const double* T = rtaps_->row(residue); const double hq = h_lp[static_cast<std::size_t>(q)];
            for (int i = 0; i < WR; ++i) row[static_cast<std::size_t>(kc - cfg_.hw_r + 1 + i - kb - s0)] += hq * T[i];
        }
    }
}

}  // namespace smlsp3000
