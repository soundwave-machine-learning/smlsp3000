# DI-001 — Machine-clock sampling-phase anchor is host-rate dependent

Status: OPEN — tracked design issue. Owner decision OWN-DEC-027 (2026-10-07): KEEP the Sprint 6 anchor unchanged for the first personal-use build. A future change requires a separately authorised DSP revision; it is not a hardware claim and not a claim of host-rate-invariant waveforms.

## Observation (Sprint 6, VAL-019 cross-rate section)

The Python reference (and the native core, which reproduces it to float rounding) anchors the SP and MPC machine clocks at proxy index 0 of the R1 output stream. Proxy index 0 corresponds to input time −lobes/fs_host (R1 group delay): 1.09 ms at 44.1 kHz, 1.00 ms at 48 kHz, 0.54 ms at 88.2 kHz, 0.50 ms at 96 kHz, 0.27 ms at 176.4 kHz, 0.25 ms at 192 kHz. The sampling phase of the machine grids relative to the audio therefore depends on the host rate. Phase-sensitive products (SP fold-back of components above 13.02 kHz, e.g. an 18 kHz tone folded to 8041.67 Hz) differ in PHASE between host rates while their magnitudes agree; in-band tones differ only by quantizer-boundary decisions.

## Reproduction

```
cmake -S native -B native/build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build native/build
python3 -m smlsp3000.runner validate-sprint6 --out research/validation --evidence evidence/sprint_06 --only VAL-019
```
Record: research/validation/rate_block/VAL-019_software.json → results.cross_rate (frozen method: 18 kHz brick wall on the source grid, Kaiser-sinc evaluation on the 44.1 kHz analysis grid, alignment by declared latency, common time origin).

## Affected fixtures and residuals (reference vs its own 44.1 kHz render; time-domain RMS re signal / magnitude-spectrum RMS re signal, dB)

| Fixture | 48 kHz | 88.2 kHz | 96 kHz | 176.4 kHz | 192 kHz |
|---|---|---|---|---|---|
| multitone_mix_m12 | -7.3 / -60.7 | -11.3 / -60.7 | -7.0 / -60.7 | -8.3 / -60.8 | -11.6 / -60.7 |
| sine_1k_m20 | -51.4 / -55.8 | -51.1 / -57.3 | -51.4 / -55.8 | -51.4 / -57.0 | -52.1 / -65.1 |
| transient_bursts | -5.9 / -44.7 | -9.9 / -52.1 | -5.5 / -50.6 | -6.9 / -50.1 | -10.2 / -57.9 |

The native core's cross-rate discrepancy equals the reference's within ≤ 4e-17 (bounded relative to the reference; no cross-rate bit identity is claimed). Phase-sensitive time-domain checks are retained alongside the magnitude view; neither replaces the other.

## Current timing / anchor model

* R1 (host→proxy, 48 lobes) output index n ↔ input time (n − 48·L)/f_proxy.
* SP machine sample k is taken at proxy position k·(f_proxy/f_SP) (+ 0 offset), MPC sample k at k·(f_proxy/44100); both clocks start at proxy index 0 of the stream (`RationalClock.reset()` → next_k = 0; `position(k) = k·period`).
* Consequence: machine sample k samples the input at time k/f_machine − 48/fs_host.

## Proposed rate-independent alternative (NOT applied)

Anchor both clocks to the input time origin: sample k at proxy position k·period + lobes·L (equivalently a capture offset of 48 host samples), so that machine sample k always samples input time k/f_machine irrespective of the host rate. Implementation: a fixed capture offset of lobes·L proxy samples in both schedulers (the scheduler already supports a capture offset in the Python reference); the hold/reconstruction edges shift by the same amount; latency bookkeeping unchanged (the offset is inside the existing look-ahead budget only if the first windows are padded accordingly — needs review).

## Expected consequences

* Compatibility: the native core and the reference would change together (same model); existing goldens (VAL-008..021) would change by phase of fold-back products and by quantizer-boundary decisions; a new asset/model version would be required, with the old evidence preserved.
* Sonic: no change in magnitude behaviour; phase of SP fold-back products relative to the audio changes (at a given host rate, by up to one SP period); on hardware this phase is arbitrary (free-running clock), so neither anchor is "more correct" than the other. Audibility is NOT asserted either way (no listening evidence).
* Not done now: no goldens regenerated, no magnitude-only substitution, no reference or native change (OWN-DEC-027).
