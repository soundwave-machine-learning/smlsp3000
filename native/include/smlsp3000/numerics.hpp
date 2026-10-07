// Numerical primitives of the native core. Every function reproduces the arithmetic ORDER of the Python/NumPy
// reference (numpy pairwise summation, numpy i0 Chebyshev evaluation, numpy sinc) so that a same-library build
// agrees with the reference to the last bit wherever libm agrees; no fast-math, no contraction (CMake sets
// -ffp-contract=off). Nothing here is machine behaviour.
#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace smlsp3000::num {

// numpy pairwise summation (numpy/core/src/umath/loops_utils.h.src, PW_BLOCKSIZE 128) applied to the products
// a[i]*b[i] (each product rounded once, as numpy's elementwise multiply does before `.sum`).
inline double pairwise_dot(const double* a, const double* b, std::size_t n) {
    if (n < 8) {
        double res = 0.0;
        for (std::size_t i = 0; i < n; ++i) res += a[i] * b[i];
        return res;
    } else if (n <= 128) {
        double r0 = a[0] * b[0], r1 = a[1] * b[1], r2 = a[2] * b[2], r3 = a[3] * b[3];
        double r4 = a[4] * b[4], r5 = a[5] * b[5], r6 = a[6] * b[6], r7 = a[7] * b[7];
        std::size_t i = 8;
        const std::size_t lim = n - (n % 8);
        for (; i < lim; i += 8) {
            r0 += a[i] * b[i];         r1 += a[i + 1] * b[i + 1];
            r2 += a[i + 2] * b[i + 2]; r3 += a[i + 3] * b[i + 3];
            r4 += a[i + 4] * b[i + 4]; r5 += a[i + 5] * b[i + 5];
            r6 += a[i + 6] * b[i + 6]; r7 += a[i + 7] * b[i + 7];
        }
        double res = ((r0 + r1) + (r2 + r3)) + ((r4 + r5) + (r6 + r7));
        for (; i < n; ++i) res += a[i] * b[i];
        return res;
    } else {
        std::size_t n2 = n / 2;
        n2 -= n2 % 8;
        return pairwise_dot(a, b, n2) + pairwise_dot(a + n2, b + n2, n - n2);
    }
}

// numpy pairwise summation of plain values.
inline double pairwise_sum(const double* a, std::size_t n) {
    if (n < 8) {
        double res = 0.0;
        for (std::size_t i = 0; i < n; ++i) res += a[i];
        return res;
    } else if (n <= 128) {
        double r[8];
        for (int j = 0; j < 8; ++j) r[j] = a[j];
        std::size_t i = 8;
        const std::size_t lim = n - (n % 8);
        for (; i < lim; i += 8)
            for (int j = 0; j < 8; ++j) r[j] += a[i + j];
        double res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
        for (; i < n; ++i) res += a[i];
        return res;
    } else {
        std::size_t n2 = n / 2;
        n2 -= n2 % 8;
        return pairwise_sum(a, n2) + pairwise_sum(a + n2, n - n2);
    }
}

// numpy.i0: Cephes Chebyshev expansions (numpy/lib/_function_base_impl.py: _i0A, _i0B, _chbevl, _i0_1, _i0_2).
inline constexpr double I0_A[30] = {
    -4.4153416464793395e-18, 3.3307945188222384e-17, -2.431279846547955e-16, 1.715391285555133e-15, -1.1685332877993451e-14,
    7.676185498604936e-14, -4.856446783111929e-13, 2.95505266312964e-12, -1.726826291441556e-11, 9.675809035373237e-11,
    -5.189795601635263e-10, 2.6598237246823866e-09, -1.300025009986248e-08, 6.046995022541919e-08, -2.670793853940612e-07,
    1.1173875391201037e-06, -4.4167383584587505e-06, 1.6448448070728896e-05, -5.754195010082104e-05, 0.00018850288509584165,
    -0.0005763755745385824, 0.0016394756169413357, -0.004324309995050576, 0.010546460394594998, -0.02373741480589947,
    0.04930528423967071, -0.09490109704804764, 0.17162090152220877, -0.3046826723431984, 0.6767952744094761};
inline constexpr double I0_B[25] = {
    -7.233180487874754e-18, -4.830504485944182e-18, 4.46562142029676e-17, 3.461222867697461e-17, -2.8276239805165836e-16,
    -3.425485619677219e-16, 1.7725601330565263e-15, 3.8116806693526224e-15, -9.554846698828307e-15, -4.150569347287222e-14,
    1.54008621752141e-14, 3.8527783827421426e-13, 7.180124451383666e-13, -1.7941785315068062e-12, -1.3215811840447713e-11,
    -3.1499165279632416e-11, 1.1889147107846439e-11, 4.94060238822497e-10, 3.3962320257083865e-09, 2.266668990498178e-08,
    2.0489185894690638e-07, 2.8913705208347567e-06, 6.889758346916825e-05, 0.0033691164782556943, 0.8044904110141088};

inline double chbevl(double x, const double* vals, int n) {
    double b0 = vals[0], b1 = 0.0, b2 = 0.0;
    for (int i = 1; i < n; ++i) { b2 = b1; b1 = b0; b0 = x * b1 - b2 + vals[i]; }
    return 0.5 * (b0 - b2);
}

inline double bessel_i0(double x) {
    x = std::fabs(x);
    if (x <= 8.0) return std::exp(x) * chbevl(x / 2.0 - 2.0, I0_A, 30);
    return std::exp(x) * chbevl(32.0 / x - 2.0, I0_B, 25) / std::sqrt(x);
}

// smlsp3000.reference.kernels.exact_sinc: numpy sinc (sin(pi x)/(pi x)) with exact 1/0 at integers.
inline double exact_sinc(double d) {
    if (d == std::round(d)) return d == 0.0 ? 1.0 : 0.0;
    const double y = 3.141592653589793 * d;   // numpy: x = pi * x; y = where(x, x, eps); sin(y)/y
    return std::sin(y) / y;
}

// smlsp3000.reference.kernels.kaiser_window_fn: arg = clip(1 - (d/hw)**2, 0, 1); i0(beta*sqrt(arg))/i0(beta).
inline double kaiser_window(double d, double half_width, double beta) {
    const double q = d / half_width;
    double arg = 1.0 - q * q;            // numpy `** 2` on float64 arrays is `square` (x*x)
    if (arg < 0.0) arg = 0.0;
    if (arg > 1.0) arg = 1.0;
    return bessel_i0(beta * std::sqrt(arg)) / bessel_i0(beta);
}

inline std::int64_t floor_div(std::int64_t a, std::int64_t b) {   // b > 0; Python // semantics
    std::int64_t q = a / b, r = a % b;
    if (r != 0 && r < 0) --q;
    return q;
}

inline std::int64_t gcd64(std::int64_t a, std::int64_t b) { if (a < 0) a = -a; if (b < 0) b = -b; while (b) { std::int64_t t = a % b; a = b; b = t; } return a; }

}  // namespace smlsp3000::num
