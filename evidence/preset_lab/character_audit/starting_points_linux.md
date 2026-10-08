# Character-audit starting points (NOT factory presets)

Rule-derived (see starting_points_linux.json); not auditioned; telemetry below from Linux renders of the synthetic demo beat. The owner re-records on real beats on Windows.

| Point | SP level | SP gain | Interstage | MPC gain | Trim | SP 12-bit clamps L/R | MPC 18-bit clamps L/R | 16-bit storage clamps L/R | Over-range | Input peak L/R (dBFS) | Output peak L/R (dBFS) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| INIT | +0.0 dB | 0 dB | +0.0 dB | LO | +0.0 dB | 0 / 0 | 0 / 0 | 0 / 0 | NO | -3.55 / -3.00 | -3.45 / -2.84 |
| SP LIGHT | +6.0 dB | 0 dB | +0.0 dB | LO | -6.0 dB | 106 / 166 | 99 / 159 | 70 / 104 | NO | -3.55 / -3.00 | -5.37 / -5.25 |
| SP HARD | +12.0 dB | 20 dB | +0.0 dB | LO | -32.0 dB | 152417 / 153168 | 53725 / 54379 | 21718 / 22210 | NO | -3.55 / -3.00 | -29.78 / -29.65 |
| MPC LIGHT | +0.0 dB | 0 dB | +6.0 dB | LO | -6.0 dB | 0 / 0 | 150 / 232 | 106 / 149 | NO | -3.55 / -3.00 | -4.89 / -4.73 |
| MPC HARD | +0.0 dB | 0 dB | +12.0 dB | MID | -32.0 dB | 0 / 0 | 258084 / 259416 | 130358 / 130864 | NO | -3.55 / -3.00 | -27.02 / -26.97 |
| DUAL LIGHT | +6.0 dB | 0 dB | +6.0 dB | LO | -12.0 dB | 106 / 166 | 14242 / 14909 | 7203 / 7556 | NO | -3.55 / -3.00 | -10.10 / -9.92 |
| DUAL MEDIUM | +12.0 dB | 0 dB | +12.0 dB | LO | -24.0 dB | 8556 / 8988 | 161131 / 162334 | 81327 / 82014 | NO | -3.55 / -3.00 | -19.89 / -19.72 |
| DUAL HARD | +12.0 dB | 20 dB | +12.0 dB | MID | -60.0 dB | 152417 / 153168 | 350281 / 350537 | 175741 / 175844 | NO | -3.55 / -3.00 | -53.88 / -54.53 |
