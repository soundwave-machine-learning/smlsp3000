# SP1200_MPC3000_MIX_PROCESSOR_RESEARCH_PACKAGE_V1

| Field | Value |
|---|---|
| Project | SP-1200 → MPC3000 Full-Mix Processor |
| Document | Research package V1 (research pass 1) |
| Date | 2026-10-05 |
| Scope | Research only. No production DSP, no plugin, no GUI, no presets, no parameter mappings |
| Hardware measured | NO |
| Simulations run | NO (closed-form arithmetic only, shown inline) |
| Listening tests | NO |
| Companion file | `SP1200_MPC3000_HANDOFF_V1.json` (summarizes this document; does not replace it) |

Reading rule for this whole document: a statement is only as strong as its status tag. "VERIFIED" here means *documentary* verification (a primary document or a published hardware measurement read directly in this pass). Nothing in this package is a measurement of a unit in our possession.

---

## 1. Executive conclusion

1. **The SP-1200 half is well enough documented to define its digital skeleton, but not its analog numbers.** Verified or strongly supported: 26.04 kHz fixed rate, 12-bit linear data, successive-approximation conversion built around the playback DAC, one DAC time-multiplexed to eight sample-and-hold channel outputs, zero-order-hold output with *no* reconstruction filter on channels 7–8, fixed low-pass filters on 3–4 and 5–6, SSM2044 dynamic filters on 1–2, mono sampling, mono mix output. Not available from anything read in this pass: every filter transfer function, every gain, every nominal level, every clip point.
2. **The best published engineering analysis says the famous SP character is mostly not in the path a mix would traverse at unity pitch.** Yeh/Nolting/Smith (CCRMA, ICMC 2007) measured an SP-12 and concluded its primary sonic characteristic is aliasing from weak output filtering plus the non-interpolating tuning algorithm; input aliasing was minor and 12-bit quantization sat near −72 dB. A full mix passed through at unity pitch gets: band-limiting near 13 kHz, a −72…−74 dB quantization error, hold droop, and (on unfiltered outputs) strong images above 13 kHz. The "drop-sample grit" appears only if the product deliberately reproduces the sample-fast/tune-down workflow, which must be labeled an extreme mode.
3. **The MPC3000 half is nominally transparent on paper.** Verified from the Akai service manual: 44.1 kHz, 16-bit linear storage, AK5328 18-bit delta-sigma ADC, SM5841 8× digital filter into PCM69A 18-bit DACs, NJM5532 and M5220L analog stages on regulated rails, digital per-voice filters. No document read in this pass identifies a coloration mechanism for line-level program at unity. Whether there is anything audible to model is a measurement question, and community opinion is split.
4. **SP → MPC interstage calibration cannot be established from documents.** SP output level is undocumented in retrieved sources. This is P0 research debt.
5. **Stereo is historical only on the MPC side.** SP-1200 sampling, voices and mix output are mono. Any stereo SP stage is a product abstraction and must be labeled as one.
6. **Verdict: HARDWARE REQUIRED.** A numerical reference of the verified digital skeleton and the schematic-extraction work can start without hardware. Production modeling cannot. Six P0 and twelve P1 items are open (section 40).

---

## 2. Product concept

`FULL MIX → SP-1200 coloration path → MPC3000 coloration path → OUTPUT`

A stereo mix-bus coloration processor. Not a sampler. The target is the cumulative effect of the conversion, filtering, analog I/O, gain staging, sample-domain representation and output architecture of the two machines.

Three product paths are researched independently and none is chosen here (CHAIN-DEC-001):

| Path | Definition | What the evidence supports today |
|---|---|---|
| A — Circuit only | Analog/electrical coloration without the sample-memory process | SP: filter and level blocks exist but have no numbers yet. MPC: op-amp stages and passive networks exist; no evidence of audible nonlinearity. Path A is currently mostly placeholders. |
| B — Full sample path | Analog in → ADC → sample representation → playback → DAC → analog out | SP: skeleton is defined (rate, word length, hold, channel filter choice). MPC: skeleton defined; contribution probably small. This is the only path whose structure is evidence-backed today. |
| C — Hybrid mix-bus | Only the stages measurements show to matter | Cannot be specified until measurements exist. It is a reduction of B, so B is the reference superset. |

---

## 3. Research methodology

1. Source search in the priority order of the brief: service manuals and schematics, manufacturer/designer documents, datasheets, published measurements, repair/teardown documentation, engineering analysis, owner reports.
2. Short factual extraction with page or drawing references. No manual reproduced.
3. Every claim tagged with an evidence class (section 4) and entered in the claim ledger (section 34).
4. Mechanisms separated into: digital, analog, converter, filtering, gain staging, nonlinearity, clock/rate, noise, aliasing.
5. No missing component value was guessed. Where a value was not reliably readable it is recorded as UNKNOWN.
6. Access failures are recorded in the failure register (section 38), not hidden.

**Access limits in this pass (important):**
- The E-mu SP-1200 service manual was located, but the public scan is image-only; its OCR layer contains watermark text only. Schematics (reported at pp. 67–88) were **not read**. SP-1200 circuit facts therefore come from secondary readings of that manual, from the designer, and from a published SP-12 study.
- The SP-12 service manual was located but retrieval was blocked.
- The Akai MPC3000 service manual OCR text **was read**: specifications, parts list, block diagrams, IC information. Schematic component values appear in the OCR but cannot be tied to nets, so no transfer function was derived.
- Datasheets: PCM69A read. AD7541, SSM2044/SSI2144, AK5328, SM5841 not retrieved in this pass.

---

## 4. Evidence taxonomy

| Class | Meaning in this package |
|---|---|
| VERIFIED | Stated in a primary document read directly in this pass (official manual text, parts list, datasheet, designer/manufacturer statement), or shown by a published hardware measurement. Documentary, not measured by us. |
| STRONGLY SUPPORTED | Multiple independent consistent sources, at least one with board-level competence, but the primary document was not read directly. |
| LITERATURE-DERIVED | Taken from a published engineering analysis or datasheet-class literature; may concern a sibling machine (SP-12). |
| SIMULATED | Result of a model or closed-form calculation. Worded as a claim about the model. |
| PROVISIONAL | Single credible source or reasoned inference; adopted as a working value and flagged replaceable. |
| SPECULATIVE | Inference without direct support. Not to be built on. |
| UNKNOWN | No usable evidence. |
| NOT EXECUTED | Experiment or measurement defined but not run. |

Promotion rule: SIMULATED never becomes a hardware claim. A simulation can verify "this model produces X", never "the hardware produces X".

Source reliability tiers (R1 best): R1 official service manual/schematic/manufacturer; R2 component datasheet; R3 published measurement or peer-reviewed analysis; R4 teardown/repair documentation and competent board-level community analysis; R5 owner reports and tertiary summaries.

---

## 5. Source register

| ID | Title | Author / maker | Year | Rev | Type | Machine | Subsystem | Tier | Access this pass | Claims supported |
|---|---|---|---|---|---|---|---|---|---|---|
| SRC-01 | SP-1200 Sampling Percussion System Service Manual | E-mu Systems | 1987 | "Revision 1, SP-1200" | Service manual + schematics | SP-1200 | All | R1 | Located; image-only scan; **schematics not read** | None directly (cited through SRC-06, 09, 11) |
| SRC-02 | SP-12 Service Manual | S. Davies, E-mu | 1985 | — | Service manual | SP-12 | All | R1 | Located; retrieval blocked | None |
| SRC-03 | SP-1200 Owner's Manual | C. Anderton, E-mu PN FI332 | 1987 | Rev. E | Owner's manual | SP-1200 | Outputs | R1 | Excerpt read | SP12-CLM-012…016 |
| SRC-04 | Physical and Behavioral Circuit Modeling of the SP-12 Sampler | Yeh, Nolting, Smith (CCRMA) | 2007 | ICMC | Published analysis + hardware measurement | SP-12 | Whole path | R3 | Read in full | SP12-CLM-001, 004, 008–013, 019 |
| SRC-05 | SP-1200 product page and FAQ | Rossum Electro-Music | 2021–2025 | — | Designer/manufacturer document | SP-1200 | Format, filters, outputs | R1 | Read | SP12-CLM-001, 003, 012–014, 025 |
| SRC-06 | "E-mu SP-1200" / "E-mu SP-12" articles | Wikipedia | 2024–2026 | — | Tertiary, cites SRC-01/02/07/08 | SP-1200 | Overview | R5 | Read | Relays 010, 012, 016, 025 |
| SRC-07 | "Why do SP-1200 channel outputs feature different analog filters?" | D. Rossum (video) | c. 2021 | — | Designer statement | SP-1200 | Output filters | R1 | Not viewed; via SRC-06 | 012–014 (indirect) |
| SRC-08 | SP-1200: The Art and Science | S. Hyland, 27Sens | 2011 | — | Book | SP-1200 | Overview | R4 | Fragments only | 005 (indirect) |
| SRC-09 | "Vintage sampler (E-mu SP1200) re-creation and improvement" | GroupDIY thread | 2014 | — | Board-level community analysis | SP-12/1200 | ADC, DAC, mux | R4 | Snippets only (fetch blocked) | 004, 006, 007, 008 |
| SRC-10 | "MKSREC 1 – 12-bit Sampling Drum Machine (My SP-1200 Clone)" | Gearspace thread | 2020 | — | Clone-builder notes | SP-1200 | Clock, SAR | R4 | Snippets | 002, 004 |
| SRC-11 | "Re-creating vintage sampler, need help with VCF" | ModWiggler thread | 2018 | — | Schematic reading by builders | SP-1200 | DAC, outputs | R4 | Snippets | 005, 021 |
| SRC-12 | "SP1200 anti aliasing filter made variable + resonance?" | GroupDIY thread | 2025 | — | Community analysis | SP-1200 | AA filters | R4 | Snippets | 008, 021 |
| SRC-13 | Owner threads on sampling gain, mono input, no monitoring | mpc-forums, Gearspace | 2005–2014 | — | Multiple owner reports | SP-12/1200 | Input | R5 | Snippets | 017, 018 |
| SRC-14 | Reissue coverage | Headliner, MusicTech | 2021 | — | Trade press quoting Rossum | SP-1200 | Reissue changes | R5 | Read | 025 |
| SRC-20 | MPC3000 Service Manual (58 pp.), incl. block diagrams No. 4-1 L401251M (8DACS), 4-3 L401253M (AD/DA), 4-4 L401254M (System/CPU); schematics No. 13-3 L401203 (AD/DA), 13-4 L401204M (8DACS) | Akai | c. 1994 | — | Service manual + schematics | MPC3000 | All | R1 | **OCR text read**; schematic values not net-resolved | MPC3K-CLM-001…014, 019 |
| SRC-21 | MPC3000 teardown gallery | N. Riehm, studiorepair.com | — | — | Teardown photographs | MPC3000 | AD/DA, 8DACS boards | R4 | Captions read | 003–005 |
| SRC-22 | PCM67 / PCM69A datasheet PDS-1168A | Burr-Brown | 1992 | A | Datasheet | MPC3000 | DAC | R2 | Read (extract) | 015 |
| SRC-23 | "18-bit D/A has good low-level performance" | EDN | 1990s | — | Trade note | MPC3000 | DAC | R5 | Read | 015 |
| SRC-24 | MPC60 Software v3.10 FAQ | Roger Linn Design | — | — | Designer statement | MPC3000 | Format, stereo | R1 | Read | 001, 002, 012 |
| SRC-25 | Akai MPC3000 review | Sound On Sound | 1994 | — | Review | MPC3000 | I/O | R5 | Read | 013 |
| SRC-26 | MPC3000 Operator's Manual, software v3.0 | Akai / R. Linn | 1994 | v3.0 | Operator's manual | MPC3000 | Sampling | R1 | Excerpt | 002 |
| SRC-27 | "Chip and OpAmp in MPC3K and S3000" | mpc-forums | 2017 | — | Owner/tech thread | MPC3000 | ADC | R5 | Read | 003 |
| SRC-28 | "Akai MPC 3000 – what makes it so special" and related | Gearspace | 2014–2026 | — | Folklore | MPC3000 | Character | R5 | Read | Conflict only |
| SRC-30 | AD7541 / AD7541A datasheet | Analog Devices | — | — | Datasheet | SP-1200 | DAC | R2 | **Not retrieved** | — |
| SRC-31 | SSM2044 / SSI2144 datasheets | SSM / Sound Semiconductor | — / 2017 | — | Datasheet | SP-1200 | Ch 1–2 | R2 | **Not retrieved** | — |
| SRC-32 | AK5328 datasheet | AKM | — | — | Datasheet | MPC3000 | ADC | R2 | **Not located** | — |
| SRC-33 | SM5841 datasheet | NPC | — | — | Datasheet | MPC3000 | Digital filter | R2 | **Not retrieved** (pin table read in SRC-20) | — |

URLs are in section 45.

### 5.1 Revision table

Incompatible revisions are not merged into one model. The reference target is a stock vintage SP-1200 and a stock MPC3000; anything else is labeled.

| Machine | Revision | Period | Documented changes | Audio-path change | Status |
|---|---|---|---|---|---|
| SP-12 | Sibling machine, not an SP-1200 revision | 1985–1987 | ROM drum sounds plus user sampling; same 26.04 kHz / 12-bit format and playback engine per SRC-05/-06 | Reported "mostly unchanged" playback electronics; not verified at schematic level (RD-P1-09) | Used only as LITERATURE-DERIVED support via SRC-04 |
| SP-1200 | Original | 1987–1990 | Service manual "Revision 1" | Baseline | VERIFIED existence |
| SP-1200 | Reissue (black chassis) | 1993–1998 | Cooler-running power supply; chassis; regulatory compliance | None documented; effect UNKNOWN | VERIFIED (SRC-06) |
| SP-1200 | "Final Edition" | 1998 | Last run before SSM2044 supply ended | None documented | VERIFIED |
| SP-1200 | E.C.O.s | — | The service manual has an E.C.O. section; not read | UNKNOWN | UNKNOWN |
| SP-1200 | Rossum 35th Anniversary Renovation | 2020 | Rebuilt originals; storage emulator; rear sliders for ch 1–2 filter cutoff; new chassis and display | Ch 1–2 initial cutoff adjustable | VERIFIED (SRC-14) |
| SP-1200 | Rossum reissue | 2021–2025 | SSI2144 replaces SSM2044; 20 s memory; SD card; separate filtered and unfiltered jacks; input monitor output; cutoff and resonance sliders | Filter IC substitution on ch 1–2; manufacturer notes some owners report very subtle differences | VERIFIED (SRC-05) |
| MPC3000 | Production unit | from 1994 | One service manual edition found; boards AD/DA L4012A502A, 8DACS L4012A502B, CPU L4012A5010 | Baseline | VERIFIED |
| MPC3000 | Options EXM3008 (memory), IB-CRT (video), I-0055 (SMPTE reader) | — | Listed in SRC-20 | None in audio path | VERIFIED |
| MPC3000 | Operating-system versions | — | Operator's manual documents software v3.0; later versions not researched to a primary source | Could affect digital arithmetic; UNKNOWN | UNKNOWN (RD-P3-02) |
| MPC3000 | Limited-edition variant | — | Not verified in this pass | UNKNOWN | UNKNOWN (RD-P3-02) |

Changes to converter parts, filter parts, PCB, op-amps, output circuitry or sample arithmetic within either machine's production run: none documented in retrieved sources; absence of evidence only.

### 5.2 Modified hardware policy

| Category | Examples | Rule |
|---|---|---|
| Aftermarket output mods | SP-1200 filter-bypass or filter-control mods, input-monitor mods | Not stock. Measurements labeled MODIFIED and excluded from the stock reference |
| Op-amp replacements | Any substitution for TL084, NJM5532, M5220L, M5238AL, µPC812C | Not stock |
| Power-supply mods and replacements | Replacement supplies in SP-1200s | Recorded in metadata; treated as stock for the audio path only if rails are verified |
| Converter or filter IC substitutions | SSI2144 in place of SSM2044 | Labeled; affects ch 1–2 only |
| Repair substitutions | Electrolytic recaps, replaced pots, replaced jacks | Recorded in metadata; recapped units are acceptable and noted |
| Third-party operating systems | Any non-Akai MPC3000 OS | Not stock for digital-path tests |
| Clones and re-creations | SRC-10 builder's unit | Never a hardware reference. Its clock reading is used only as a PROVISIONAL pointer to the original circuit |

Every measured unit carries a modification status in its metadata before any capture is accepted.

---

## 6. SP-1200 architecture

Actual topology as far as evidence allows (replaces the conceptual chain in the brief):

```
SAMPLE IN (single mono jack)                                   [STRONGLY SUPPORTED]
  → switchable preamp, 0 / +20 / +40 dB                        [STRONGLY SUPPORTED, owner reports]
  → fixed active low-pass anti-alias filter, TL084 op-amps     [STRONGLY SUPPORTED; order, corner UNKNOWN]
  → sample-and-hold at 26.04 kHz                               [LITERATURE-DERIVED from SP-12]
  → 12-bit successive approximation: SAR logic + comparator
     + the same DAC that is used for playback                  [STRONGLY SUPPORTED]
  → 12-bit linear words in RAM                                 [VERIFIED]
  → playback: table read with truncated fractional index
     (drop/repeat sample), fixed 26.04 kHz output rate         [VERIFIED]
  → AD7541 12-bit multiplying DAC, shared by all 8 voices,
     updated 8× per sample period                              [STRONGLY SUPPORTED]
  → per-voice level via an 8-bit multiplying DAC that uses
     the 12-bit DAC output as its reference                    [PROVISIONAL, single source]
  → 8-way multiplexer → one hold capacitor per channel
     (zero-order hold)                                         [STRONGLY SUPPORTED]
  → per-channel output filter:
        ch 1–2  SSM2044 4-pole low-pass, cutoff swept by an
                envelope started at note trigger, fixed Q      [VERIFIED / LITERATURE-DERIVED]
        ch 3–4  fixed low-pass, lower corner                   [VERIFIED; values UNKNOWN]
        ch 5–6  fixed low-pass, higher corner                  [VERIFIED; values UNKNOWN]
        ch 7–8  no filter                                      [VERIFIED]
  → individual output jack (filtered contact and unfiltered
     contact for ch 1–6)                                       [VERIFIED; contact mapping in conflict]
  → MIX OUT: mono sum of the eight channels, MIX VOLUME pot    [VERIFIED; summing point UNKNOWN]
```

There is no VCA in the classical sense and no reconstruction filter stage common to all voices. A tertiary source claiming "ADSR + analog VCA per voice" is unsupported (conflict ledger C-04).

Workflow mechanisms that are sampler features and not signal-path coloration: 2.5 s per sound, 10 s total, truncate/loop, decay envelope, velocity, sequencer. These are out of scope (CHAIN-DEC-016).

---

## 7. SP-1200 circuit map

| Block | Parts | Topology | Rails | Nominal / max level | Gain | Zin / Zout | Response | Noise / THD / IMD | Clip | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Input jack + preamp | UNKNOWN (op-amp stage) | Switchable gain | UNKNOWN | UNKNOWN | 0 / +20 / +40 dB | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Gain steps STRONGLY SUPPORTED; rest UNKNOWN |
| AA filter | TL084 sections | Active low-pass, multi-section | UNKNOWN | UNKNOWN | UNKNOWN | — | SP-12: attenuates above ~15 kHz (SRC-04) | UNKNOWN | UNKNOWN | PARTIAL |
| S/H + SAR ADC | SAR logic, comparator, AD7541 | Successive approximation | UNKNOWN | FS voltage UNKNOWN | — | — | Aperture UNKNOWN | Ideal 12-bit ≈ 74 dB SQNR | Code clamp presumed; "sample clear" indication reported | PARTIAL |
| DAC | AD7541 | CMOS R-2R multiplying, current out, I/V op-amp | UNKNOWN | UNKNOWN | — | — | Settling vs 4.8 µs slot UNKNOWN | Grade fitted UNKNOWN | — | PARTIAL |
| Level DAC | 8-bit multiplying DAC | Reference = audio | UNKNOWN | — | 0…max, unity point UNKNOWN | — | — | UNKNOWN | — | PROVISIONAL |
| Mux + hold | Analog mux, hold caps | 8-channel S/H | UNKNOWN | — | — | — | Hold fraction UNKNOWN; droop/feedthrough UNKNOWN | UNKNOWN | — | PARTIAL |
| Ch 1–2 filter | SSM2044 | 4-pole ladder-type VCF, envelope-swept | UNKNOWN | — | — | — | Time-varying | UNKNOWN | UNKNOWN | PARTIAL |
| Ch 3–4, 5–6 filters | TL084 | Fixed active low-pass | UNKNOWN | — | — | — | Corners UNKNOWN | UNKNOWN | UNKNOWN | PARTIAL |
| Mix amp + volume | UNKNOWN | Summing | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

Level dependency, frequency dependency, channel interaction, slew limits, phase response: all UNKNOWN pending schematic extraction (CHAIN-EXP-019) and hardware measurement.

### 7.1 Component ledger (SP-1200)

Reference designators and schematic sheet numbers are UNKNOWN because SRC-01 was not read; schematics are reported at manual pp. 67–88 (SRC-11).

| Block | Ref des | Part | Type | Function | Datasheet | Supply | Surrounding components | Expected audio effect | Evidence | Implementation impact |
|---|---|---|---|---|---|---|---|---|---|---|
| Clock | UNKNOWN | 20 MHz oscillator, ÷3, ÷256 | Crystal + logic | Sample clock 26 041.67 Hz | — | +5 V | Flip-flops, counters | Defines sampling grid | PROVISIONAL (SRC-10) | SP rate constant |
| Input preamp | UNKNOWN | UNKNOWN op-amp | Amplifier | 0 / +20 / +40 dB | — | UNKNOWN | Gain-switch network | Gain; possible clip | STRONGLY SUPPORTED (gain steps) | R2 |
| AA filter | UNKNOWN | TL084 | Quad JFET op-amp | Multi-section low-pass | Not retrieved | UNKNOWN | R/C values UNKNOWN | Band limit, phase near edge, fold-back | STRONGLY SUPPORTED | R3 |
| Sample-and-hold | UNKNOWN | UNKNOWN | S/H | Holds input during conversion | — | UNKNOWN | Hold capacitor | Aperture | LITERATURE-DERIVED (SP-12) | R4 |
| SAR | UNKNOWN | Successive-approximation register (a 74-series "504"-type part is reported; unverified) | Logic | Drives DAC during conversion | — | +5 V | Comparator | Quantizer rule | STRONGLY SUPPORTED (function); part UNKNOWN | R5 |
| Comparator | UNKNOWN | UNKNOWN | Comparator | SAR decision | — | UNKNOWN | — | Offset, noise (self-dither) | UNKNOWN | R5 |
| DAC | UNKNOWN | AD7541 | 12-bit CMOS multiplying DAC | Playback and SAR feedback | SRC-30, not retrieved | UNKNOWN | I/V op-amp, reference | Static transfer | STRONGLY SUPPORTED | R5, R7 |
| Level DAC | UNKNOWN | 8-bit multiplying DAC (part UNKNOWN) | Multiplying DAC | Per-voice level and decay | — | UNKNOWN | — | Gain only at fixed level | PROVISIONAL | R6 |
| Mux and hold | UNKNOWN | Analog multiplexer + 8 hold capacitors | S/H | Demultiplex to channels | — | UNKNOWN | Buffers | Hold response, feedthrough spurs | STRONGLY SUPPORTED | R7 |
| Ch 1–2 filter | UNKNOWN | SSM2044 ×2 | 4-pole VCF IC | Envelope-swept low-pass | SRC-31, not retrieved | UNKNOWN | Envelope circuit, trimmers | Time-varying low-pass | VERIFIED | Excluded |
| Ch 3–6 filters | UNKNOWN | TL084 | Quad JFET op-amp | Fixed low-pass, two corners | Not retrieved | UNKNOWN | R/C values UNKNOWN | Image attenuation, HF response | STRONGLY SUPPORTED | R8 |
| Mix amp | UNKNOWN | UNKNOWN | Summing amplifier | Mono mix, volume | — | UNKNOWN | MIX VOLUME pot | Gain, coupling pole | VERIFIED (function) | R9 |

### 7.2 Circuit extraction (SP-1200)

No resistor or capacitor value was readable in this pass. Filter transfer functions, corner frequencies, Q, gains, impedances, DC operating points, clipping limits and coupling poles: **UNKNOWN**. Nothing is guessed. The only derivations possible are from the digital format and are shown in sections 8 and 11.

---

## 8. SP-1200 digital path

| Item | Finding | Status |
|---|---|---|
| Nominal sample rate | 26.04 kHz, identical for record and playback | VERIFIED (SRC-05) |
| Clock-derived rate | 20 MHz ÷ 3 ÷ 256 = 20 000 000 / 768 = **26 041.67 Hz** (period 38.4 µs) | PROVISIONAL (SRC-10 clone-builder reading; consistent with a measured ~26 kHz tone on an SP-12 in SRC-04) |
| ADC resolution | 12 bits, successive approximation | STRONGLY SUPPORTED |
| Stored resolution | 12-bit linear | VERIFIED |
| DAC resolution | 12 bits (AD7541) | STRONGLY SUPPORTED |
| Level scaling resolution | 8-bit multiplying DAC, analog domain | PROVISIONAL |
| Encoding, signed/unsigned | UNKNOWN (offset binary is typical for a unipolar SAR, not confirmed) | UNKNOWN |
| Quantizer rounding rule | UNKNOWN. A SAR settles on the largest code whose DAC level does not exceed the input, i.e. floor relative to comparator offset; half-LSB offset trim UNKNOWN | UNKNOWN |
| Dither | No evidence of deliberate dither. Analog noise at the comparator may self-dither | UNKNOWN |
| Playback arithmetic | Table index with fractional increment; fractional part truncated; no interpolation | VERIFIED (SRC-05 "drop-sample"), LITERATURE-DERIVED detail (SRC-04) |
| Accumulator precision | UNKNOWN | UNKNOWN |
| Pitch / rate relationship | Output rate fixed; pitch changes by skipping or repeating samples. Tuning in semitone steps (SP-12) | VERIFIED / LITERATURE-DERIVED |
| Digital mixing | None. Voices are separate analog channels summed after conversion | STRONGLY SUPPORTED |
| Digital headroom | No digital gain stage identified, so headroom is the ADC code range | PROVISIONAL |
| Digital clipping | Clamp at code limits presumed; machine reports whether clipping occurred during sampling | PROVISIONAL (owner report) |

ADC bits = stored bits = DAC bits = 12 on this machine, each supported separately above. The only extra word length is the 8-bit *analog-domain* level DAC.

Arithmetic:
- Ideal 12-bit SQNR = 6.02 × 12 + 1.76 = **74.0 dB**. One LSB = 20·log10(1/4096) = −72.2 dB re full scale. SRC-04 uses 72 dB.
- Multiplexed DAC update rate = 8 × 26 041.67 = 208 333 Hz; one slot = 4.8 µs.

---

## 9. SP-1200 converters

**One converter does both jobs.** The AD7541 is the playback DAC and the feedback DAC of the successive-approximation ADC.

| Property | Datasheet capability | Behavior installed in the SP-1200 |
|---|---|---|
| Architecture | CMOS R-2R current-output multiplying DAC, 12-bit (recalled; SRC-30 not retrieved, so LITERATURE-DERIVED and to be confirmed) | Used with an I/V op-amp; reference arrangement UNKNOWN |
| INL / DNL | Grade dependent, order of ±½ to ±1 LSB (recalled, unconfirmed) | Grade fitted UNKNOWN. Measured transfer NOT EXECUTED |
| Settling | Order of 1 µs class (recalled, unconfirmed) | Must settle inside a 4.8 µs slot including I/V amp and mux. Margin UNKNOWN |
| Glitch | Code-dependent glitch at major carries (generic to R-2R) | Deglitched by the per-channel sample-and-hold if the hold is strobed after settling. Timing UNKNOWN |
| Zero-crossing behavior | Mid-scale major carry is the worst-case DNL/glitch code for offset-binary audio | Relevance UNKNOWN |
| Noise, HF distortion | Not specified for audio | UNKNOWN |

Inference to test, not to build on (SP12-CLM-026, SPECULATIVE): because the same DAC defines the ADC thresholds and the playback levels, its static nonlinearity should largely cancel for a signal recorded and played back at the same code. If true, a measured-INL model would be unnecessary complexity for the record/playback round trip, and the residual would be local step-size variation. CHAIN-EXP-002 and -003 test this.

Do not model datasheet imperfections by default (CHAIN-DEC-011).

---

## 10. SP-1200 input electronics

| Item | Finding | Status |
|---|---|---|
| Connector | Single SAMPLE IN jack, mono | STRONGLY SUPPORTED |
| Coupling | UNKNOWN | UNKNOWN |
| Gain | Menu-selected 0 / +20 / +40 dB | STRONGLY SUPPORTED |
| Filter | Multi-section active low-pass on TL084 | STRONGLY SUPPORTED |
| Filter order, corner, Q, ripple, stopband | UNKNOWN for SP-1200. For SP-12, SRC-04 reports attenuation above ~15 kHz and needed an order-11 digital fit at 96 kHz to match the SPICE response (fit order, not analog order) | UNKNOWN / LITERATURE-DERIVED |
| Pre-emphasis | None found | UNKNOWN |
| Input impedance, nominal level, rails, headroom, clip point, LF corner, slew, THD | UNKNOWN | UNKNOWN |
| Monitoring | Originals have no input monitor; the 2021 reissue adds a monitor tap described as "the output of the input filter and amplifier" | VERIFIED (SRC-14) |

Consequence of a ~15 kHz filter edge against a 13.02 kHz Nyquist frequency: content between 13.02 and ~15 kHz is not fully removed and folds to 11.0–13.0 kHz (26 041.67 − 15 000 = 11 041.67 Hz; 26 041.67 − 14 000 = 12 041.67 Hz). SRC-04 judged this a minor contributor on drums. On bright full mixes its magnitude is UNKNOWN.

---

## 11. SP-1200 output electronics

Ideal zero-order hold at 26 041.67 Hz (SIMULATED: these numbers describe an ideal full-period hold, not the hardware, whose hold fraction is UNKNOWN):

| Frequency | sinc magnitude |
|---|---|
| 1 kHz | −0.02 dB |
| 5 kHz | −0.53 dB |
| 8 kHz | −1.39 dB |
| 10 kHz | −2.22 dB |
| 12 kHz | −3.28 dB |
| 13.02 kHz (Nyquist) | −3.92 dB |
| 16 kHz | −6.29 dB |
| 20 kHz | −11.18 dB |

Formula: |H(f)| = |sin(πf/fs) / (πf/fs)|, fs = 26 041.67 Hz.

Images on an unfiltered channel: a 10 kHz component produces an image at 26 041.67 − 10 000 = 16 041.67 Hz at about −6.3 dB re the ideal-hold DC gain, only ~4.1 dB below the 10 kHz fundamental (−2.22 dB). A 6 kHz component images at 20 041.67 Hz at about −11.2 dB. These images are inside the audio band. Rossum describes the missing reconstruction filter as deliberate and as the source of a brighter sound (SRC-05/06, VERIFIED as a designer statement). SRC-04 observed the images on an SP-12 unfiltered channel (LITERATURE-DERIVED).

Filters, op-amps, gain, rails, headroom, clip point, output impedance, coupling: UNKNOWN beyond "TL084-based" (STRONGLY SUPPORTED) and SRC-04's order-5 digital fit at 48 kHz for an SP-12 output filter.

---

## 12. SP-1200 output comparison

| Path | DAC | Filtering | Level control | Summing | Op-amps | Gain, coupling, Z, noise, THD, headroom |
|---|---|---|---|---|---|---|
| Ch 1–2 filtered | Shared AD7541 + hold | SSM2044, envelope-swept, fixed Q | Level DAC | — | UNKNOWN | UNKNOWN |
| Ch 3–4 filtered | same | Fixed low-pass, lower corner | same | — | TL084 | UNKNOWN |
| Ch 5–6 filtered | same | Fixed low-pass, higher corner | same | — | TL084 | UNKNOWN |
| Ch 7–8 | same | None | same | — | UNKNOWN (buffer) | UNKNOWN |
| Ch 1–6 unfiltered contact | same | None (pre-filter tap) | same | — | UNKNOWN | UNKNOWN |
| MIX OUT | same | Sum of channels; whether post-filter and whether ch 7–8 enter unfiltered is UNKNOWN (likely post-filter) | MIX VOLUME | Mono | UNKNOWN | UNKNOWN |
| Headphone | None on the original (no evidence of one) | — | — | — | — | UNKNOWN |

Rule adopted: components from different output paths are never merged into one chain. The reference model carries the output filter as a selected, replaceable block (CHAIN-DEC-003). Channels 1–2 are excluded from the MVP because their filter is retriggered per note and has no defined behavior for continuous program.

---

## 13. SP-1200 sonic contribution ranking (unity-pitch mix path)

| Rank | Contributor | Evidence class | Expected magnitude | Expected audibility | Hardware need | Candidate strategy | MVP |
|---|---|---|---|---|---|---|---|
| 1 | Sample rate / band limit (~13 kHz) | VERIFIED | Removes or folds everything above ~13 kHz | Likely audible on any full mix | Confirm corner | Machine-rate domain | Yes |
| 2 | Reconstruction choice: hold + images vs channel filter | VERIFIED + SIMULATED | Images within 4–11 dB of source components at 13–20 kHz on unfiltered path | Likely audible | Measure per output | ZOH at high internal rate + replaceable output filter | Yes |
| 3 | Anti-alias filter shape | LITERATURE-DERIVED | Passband ripple, droop, group delay near band edge; fold-back from 13–15 kHz | Likely audible on bright material | Yes | Linear filter from SPICE or measurement | Yes (placeholder until values exist) |
| 4 | Gain staging / clipping at ADC | PROVISIONAL | Hard limit at code range if driven | Audible only when driven | Yes | Explicit clamp at calibrated level | Yes (boundary only) |
| 5 | Quantization (12-bit) | VERIFIED / computed | Error ≈ −72…−74 dB re FS; signal-correlated on low-level or simple signals | Subtle on dense mixes at high level; audible on fades and quiet passages | Low-level sine test | Ideal quantizer | Yes |
| 6 | Hold droop | SIMULATED | −2.2 dB at 10 kHz (ideal) | Subtle to audible | Confirm hold fraction | Falls out of ZOH | Yes |
| 7 | Pitch-dependent aliasing (drop-sample) | VERIFIED mechanism | Large when tuned | Not present at unity | — | Separate extreme mode | No |
| 8 | Output amplifier / mix amp | UNKNOWN | UNKNOWN | UNKNOWN | Yes | L0 placeholder | Placeholder |
| 9 | Input amplifier nonlinearity | UNKNOWN | UNKNOWN | UNKNOWN | Yes | L0 placeholder | Placeholder |
| 10 | DAC / ADC static error | SPECULATIVE (may cancel) | Probably small | Probably inaudible | Transfer test | None unless measured | No |
| 11 | Level DAC resolution | PROVISIONAL | None at fixed level | None | — | Omit | No |
| 12 | Noise (analog, mux feedthrough) | UNKNOWN | UNKNOWN | UNKNOWN | Yes | Omit until measured | No |
| 13 | Clocking / jitter | No evidence of an effect | — | — | Spectral check | Reject | No |
| 14 | Crosstalk between channels | UNKNOWN | UNKNOWN | UNKNOWN | Stereo tests | Omit | No |
| 15 | SSM2044 dynamic filter | VERIFIED exists | Large but note-triggered | Not applicable to continuous program | — | Out of MVP | No |

---

## 14. MPC3000 architecture

Actual topology from the Akai service manual block diagrams and parts list (SRC-20):

```
RECORD IN L / R (3-pole phone jacks J102, J103; 45 kΩ)         [VERIFIED parts/spec; balanced topology not confirmed]
  → input amplifiers: M5238AL (IC103, IC104), M5220L (IC101,
     IC102), µPC812C (IC105); 3-position gain switch SW101
     (LOW / MID / HIGH); dual 10 kΩ RECORD LEVEL pot           [VERIFIED parts; stage order PARTIAL]
  → AK5328-VP (IC106): 18-bit stereo delta-sigma ADC with
     64 fs oversampling digital decimation filter              [VERIFIED]
  ┆ alternative source: S/PDIF DIGITAL IN (RCA J101) → YM3623B
  ┆ receiver (16-bit data out), 44.1 kHz only                  [VERIFIED]
  → 16-bit linear words in wave RAM (data bus W0–W15)          [VERIFIED]
  → Akai L7A1045 "L6028 DSP-A" 18-bit DSP: 32 voices, pitch,
     per-voice 12 dB/oct resonant low-pass, envelopes, level,
     pan, mix to stereo bus and 8 individual buses; a port
     for a "second LSI"                                        [VERIFIED function list; arithmetic UNKNOWN]
  → serial 18-bit data, separate word clocks for L/R mix and
     for individual pairs 0/1, 2/3 …                           [VERIFIED]
  MAIN: SM5841HP (IC108) 8× oversampling digital filter
     → PCM69AP (IC109) dual 18-bit DAC, current out
     → NJM5532D (IC110) I/V
     → M5220L (IC111–IC113) low-pass filter and buffers
     → mute relay RL101 → STEREO OUT L/R (2-pole jacks J104, J105)
     → M5216L (IC114) → PHONES (J106)                          [VERIFIED parts and block order]
  INDIVIDUAL (8DACS board): 4× SM5841HP (IC301–304)
     → 4× PCM69AP (IC305–308) → 4× NJM5532D (IC309–312) I/V
     → 8× M5220L (IC313–320) low-pass + buffer
     → 100 Ω (R429–R436) → 8 two-pole jacks J301–J308          [VERIFIED parts and block order; 100 Ω as series build-out PROVISIONAL]
```

All filtering per voice is digital. There is no analog VCF and no analog VCA in the parts list (STRONGLY SUPPORTED by absence in SRC-20).

---

## 15. MPC3000 circuit map

| Block | Parts (ref des) | Topology | Rails | Level | Gain | Zin / Zout | Response | Noise / THD | Clip | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Record input | M5238AL ×2, M5220L ×2, µPC812C, SW101, VR701/702 | Multi-stage with switched gain and level pot | ±12 V regulated (NJM7812FA / NJM7912FA on power board) PROVISIONAL assignment | Sensitivity HI −58, MID −38, LO −18 dBs (0 dBs = 0.775 Vrms) | 20 dB steps between positions | 45 kΩ in | UNKNOWN | UNKNOWN | UNKNOWN | PARTIAL |
| ADC | AK5328-VP | Delta-sigma, 64× | ±5 V / +5 V local (µPC7805HF, NJM7905FA, LM2940CT-5.0) PROVISIONAL assignment | FS input voltage UNKNOWN (datasheet not located) | — | — | Decimation filter response UNKNOWN | UNKNOWN | Digital full scale; overload behavior of modulator UNKNOWN | PARTIAL |
| Digital filter | SM5841HP | 8× FIR interpolator, 18-bit in, 384 fs or 256 fs clock, de-emphasis select pins | +5 V | — | — | — | Response and group delay UNKNOWN (datasheet not retrieved) | — | — | PARTIAL |
| DAC | PCM69AP-4 | 10-bit ladder DAC + 1-bit first-order noise-shaped DAC, co-phase dual | Single +5 V | 0…1.2 mA out (±3 %) | — | 1.8 kΩ out (±30 %) | — | Dynamic range 106 dB (THD+N at −60 dB); max THD+N −92 dB; SNR 110 dB | — | VERIFIED (datasheet); "-4" suffix meaning UNKNOWN |
| I/V | NJM5532D | Transimpedance | ±12 V PROVISIONAL | Feedback R UNKNOWN, so FS voltage UNKNOWN | — | — | — | — | Rail-limited | PARTIAL |
| Output filter + buffer | M5220L | Active low-pass, order UNKNOWN | ±12 V PROVISIONAL | Stereo and individual out "6 dBm / 600 Ω" as printed | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PARTIAL |
| Mute | RL101 relay (main) | Series/shunt UNKNOWN | — | — | — | — | — | — | — | PARTIAL |

The OCR of schematics 13-3 and 13-4 shows resistor values such as 10 kΩ(F), 11 kΩ(D), 15 kΩ(D), 4.3 kΩ(F) and capacitors 560 pF, 220 pF, 100 pF, 0.0047 µF, 22 µF/25 V, 47 µF/25 V around the DAC output stages. They cannot be assigned to nets from OCR, so **no corner frequency is derived** (section 38, F-04). They are legible in the scan; manual extraction is feasible and is CHAIN-EXP-020.

### 15.1 Component ledger (MPC3000)

Schematic references: AD/DA schematic No. 13-3 (L401203), 8DACS schematic No. 13-4 (L401204M); block diagrams No. 4-3 (L401253M) and 4-1 (L401251M). All from SRC-20.

| Block | Ref des | Part | Type | Function | Datasheet | Supply | Surrounding components | Expected audio effect | Evidence | Implementation impact |
|---|---|---|---|---|---|---|---|---|---|---|
| Record input | IC103, IC104 | M5238AL | Dual FET-input op-amp | Input amplification | Not retrieved | ±12 V PROVISIONAL | SW101 gain switch | Gain, noise, clip | VERIFIED part | R11 |
| Record input | IC101, IC102 | M5220L | Dual low-noise op-amp | Input stage / ADC drive | Not retrieved | ±12 V PROVISIONAL | VR701/702 dual 10 kΩ | Gain, filter | VERIFIED part | R11 |
| Record input | IC105 | µPC812C | Dual JFET op-amp | Input chain (exact role unresolved) | Not retrieved | ±12 V PROVISIONAL | — | — | VERIFIED part | R11 |
| Gain switch | SW101 | 3-position slide | Switch | LOW / MID / HIGH | — | — | — | 20 dB steps | VERIFIED | R11 |
| ADC | IC106 | AK5328-VP | 18-bit stereo delta-sigma ADC, 64 fs | A/D conversion | SRC-32, not located | 5 V local | Reference decoupling | Band edge, full-scale clip | VERIFIED | R12 |
| Digital in | IC905 | YM3623B | S/PDIF receiver | Digital sampling input | — | +5 V | — | None on analog path | VERIFIED | Test route |
| DSP | IC28 | L7A1045 L6028 DSP-A | Akai custom 18-bit DSP | Voice engine and mixer | None public | +5 V | Wave RAM, 33.8688 MHz clock | Arithmetic | VERIFIED part | R13, R14 |
| Clock | X2 | 33.8688 MHz crystal | Crystal | 768 fs master clock | — | — | — | Sampling grid | VERIFIED | MPC rate |
| Digital filter (main) | IC108 | SM5841HP | 8× oversampling FIR | Interpolation | SRC-33, not retrieved | +5 V | — | Band edge, ringing, latency | VERIFIED | R15 |
| DAC (main) | IC109 | PCM69AP-4 | Dual 18-bit DAC | D/A conversion | SRC-22 | +5 V | Servo and reference filter capacitors | Converter linearity | VERIFIED | R15 |
| I/V (main) | IC110 | NJM5532D | Dual low-noise op-amp | Current-to-voltage | Not retrieved | ±12 V PROVISIONAL | Feedback R and C UNKNOWN | Gain, first pole | VERIFIED part | R15 |
| Filter / buffer (main) | IC111–IC113 | M5220L | Dual low-noise op-amp | Low-pass and output buffer | Not retrieved | ±12 V PROVISIONAL | R/C not net-resolved | HF response, coupling pole | VERIFIED part | R15 |
| Mute | RL101 | G5A-237P relay | Signal relay | Output mute | — | 12 V | — | None when closed | VERIFIED part | — |
| Phones | IC114 | M5216L | Dual op-amp (driver) | Headphone amplifier | Not retrieved | ±12 V PROVISIONAL | — | Not in line path | VERIFIED part | — |
| Digital filter (individual) | IC301–IC304 | SM5841HP | 8× FIR | Interpolation | SRC-33 | +5 V | — | As main | VERIFIED | R15 variant |
| DAC (individual) | IC305–IC308 | PCM69AP-4 | Dual 18-bit DAC | D/A conversion | SRC-22 | +5 V | — | As main | VERIFIED | R15 variant |
| I/V (individual) | IC309–IC312 | NJM5532D | Dual op-amp | Current-to-voltage | Not retrieved | ±12 V PROVISIONAL | — | As main | VERIFIED part | R15 variant |
| Filter / buffer (individual) | IC313–IC320 | M5220L | Dual op-amp | Low-pass and buffer | Not retrieved | ±12 V PROVISIONAL | R429–R436 100 Ω | As main; 100 Ω source resistance PROVISIONAL | VERIFIED part | R15 variant |
| Regulators | IC802, IC803; IC115–IC117; IC321, IC322 | NJM7812FA, NJM7912FA; µPC7805HF, NJM7905FA, LM2940CT-5.0; LM2940CT-5.0 | Linear regulators | Analog and converter rails | — | — | Zeners HZS12B2, HZS5C2 | None expected | VERIFIED parts | No supply model |

### 15.2 Circuit extraction (MPC3000)

Derivations possible from retrieved values:

- Input sensitivity in volts, 0 dBs = 0.775 Vrms: −18 dBs → 0.775 × 10^(−18/20) = 97.6 mVrms (138 mV peak); −38 dBs → 9.76 mVrms; −58 dBs → 0.976 mVrms.
- Output level if "6 dBm" means +6 dBm into 600 Ω: 0.775 × 10^(6/20) = 1.546 Vrms = 2.19 V peak. PROVISIONAL because the sign is not legible.
- DAC full-scale voltage after I/V: V = 1.2 mA × R_feedback (peak-to-peak span). R_feedback is **UNKNOWN**, so no voltage is stated.
- Filter corner frequencies, Q, coupling poles, clipping limits, DC operating points: **UNKNOWN**. Component values are visible in the scan but not attributable to nets from OCR. Not guessed.

---

## 16. MPC3000 digital path

| Item | Finding | Status |
|---|---|---|
| Sample rate | 44.1 kHz; stated response 20 Hz – 20 kHz | VERIFIED |
| Master clock | 33.8688 MHz crystal = 768 × 44.1 kHz; DSP "system clock input (768 times the sampling rate)" | VERIFIED |
| ADC resolution | 18 bits | VERIFIED |
| Stored resolution | 16-bit linear | VERIFIED |
| 18 → 16 bit reduction | Truncation, rounding or dither: UNKNOWN | UNKNOWN |
| DAC resolution | 18 bits, fed by an 18-bit-input 8× digital filter | VERIFIED |
| DSP word length | Described as "18 bit digital signal processor"; internal accumulator width UNKNOWN | PARTIAL |
| Gain / pan arithmetic, rounding | UNKNOWN | UNKNOWN |
| Interpolation for pitch | UNKNOWN | UNKNOWN |
| Unity playback bit-transparency | UNKNOWN. Because output is 18-bit, any level below maximum yields sub-16-bit detail at the DAC | UNKNOWN |
| Per-voice filter | 12 dB/oct dynamic resonant low-pass, digital | VERIFIED spec |
| Stereo sampling | True phase-locked stereo | VERIFIED (SRC-24) |
| Digital input | S/PDIF, 44.1 kHz only | VERIFIED |
| Digital headroom / clipping in mixer | UNKNOWN (32 voices summed; scaling UNKNOWN) | UNKNOWN |
| De-emphasis | SM5841 de-emphasis control lines (DSF1, DSF2) are wired; when they are asserted is UNKNOWN | PARTIAL |

"16-bit / 44.1 kHz" describes storage only. Conversion is 18-bit at both ends, and output word length is 18 bits.

Arithmetic: ideal SQNR 16-bit = 98.1 dB; 18-bit = 110.1 dB.

---

## 17. MPC3000 converters

| Converter | Part | Architecture | Datasheet facts obtained | System behavior |
|---|---|---|---|---|
| ADC | AKM AK5328-VP | 18-bit stereo delta-sigma, 64 fs oversampling, on-chip decimation filter | Only the service-manual description. Datasheet not located: dynamic range, S/(N+D), FS input, filter ripple, stopband, group delay all UNKNOWN | Preceded by Akai input stages; analog anti-alias requirement is relaxed by 64× oversampling (a low-order filter is sufficient in principle; actual order UNKNOWN) |
| Digital filter | NPC SM5841HP | 8 fs oversampling FIR, 18-bit input, 384/256 fs system clock, de-emphasis, DC offset add pin | Pin functions from SRC-20 | Sets the in-band reconstruction response and most DAC-side latency; values UNKNOWN |
| DAC | Burr-Brown PCM69AP-4 | Hybrid: 10-bit DAC + 1-bit first-order noise-shaped DAC, digital offset with analog correction; dual co-phase | 18-bit; single +5 V; 0–1.2 mA; 1.8 kΩ; DR 106 dB; max THD+N −92 dB; SNR 110 dB; runs at 384 fs, 256 fs etc. | Operated at 8 fs data from SM5841 with 384 fs clock (16.9344 MHz) PROVISIONAL; followed by 5532 I/V and active low-pass |

Converter capability is at or beyond 16-bit storage resolution, so on paper the 16-bit word is the limiting element. Installed performance is NOT EXECUTED.

---

## 18. MPC3000 input electronics

| Item | Finding | Status |
|---|---|---|
| Connectors | Two 3-pole 6.3 mm jacks (L, R) | VERIFIED part type |
| Input impedance | 45 kΩ | VERIFIED |
| Sensitivity | HI −58 dBs (0.98 mVrms), MID −38 dBs (9.76 mVrms), LO −18 dBs (97.6 mVrms) | VERIFIED text; computed volts |
| Level control | Dual 10 kΩ pot, audio taper | VERIFIED part |
| Op-amps | M5238AL (FET-input dual), M5220L (low-noise dual), µPC812C (JFET dual) | VERIFIED part numbers; device characteristics recalled, datasheets not retrieved |
| Coupling, filter order, rails per stage, max input level, clip point, response, phase, noise, THD | UNKNOWN | UNKNOWN |

Reading of the sensitivity figure: "sensitivity" is the input level that reaches reference recording level with RECORD LEVEL at maximum. Even LO gain reaches reference at 97.6 mVrms, so any line-level source needs the pot turned well down. Where overload occurs first (a stage before the pot, or the ADC) is UNKNOWN and decides whether analog input clipping exists as a mechanism at all.

---

## 19. MPC3000 output electronics

Chain: PCM69A current output (0–1.2 mA, 1.8 kΩ) → NJM5532D transimpedance stage → M5220L active low-pass → M5220L buffer → (relay on main) → jack.

| Item | Finding | Status |
|---|---|---|
| Filter topology and order | UNKNOWN (values legible in scan, not extracted) | UNKNOWN |
| Rails | ±12 V regulated PROVISIONAL | PROVISIONAL |
| Output level | "6 dBm / 600 Ω" as printed. If this means +6 dBm: 1.546 Vrms, 2.19 V peak. Sign not legible in OCR | PROVISIONAL |
| Full-scale output voltage | UNKNOWN | UNKNOWN |
| Output impedance | 100 Ω series resistor on individual outs PROVISIONAL; main UNKNOWN | PROVISIONAL |
| Coupling | Electrolytics 22 µF and 47 µF, 25 V present near outputs; LF pole UNKNOWN without the load and series values | UNKNOWN |
| Clip behavior | Rail-limited op-amps far above DAC full scale on ±12 V is plausible; not confirmed | SPECULATIVE |
| Noise, distortion, phase | UNKNOWN | UNKNOWN |

---

## 20. MPC3000 output comparison

| Aspect | Main stereo out | Individual / assignable outs | Headphone |
|---|---|---|---|
| Digital source | DSP stereo mix bus | DSP individual buses, with independent mix levels (SRC-24) | Same as main |
| Digital filter | 1× SM5841HP | 4× SM5841HP | — |
| DAC | 1× PCM69AP (dual) | 4× PCM69AP (dual), one per output pair | — |
| I/V | NJM5532D | NJM5532D | — |
| Filter / buffer | M5220L ×3 | M5220L ×8 | M5216L driver |
| Muting | Relay RL101 | Mute line to digital filters; no relay in parts list | — |
| Jack | 2-pole | 2-pole | 3-pole |
| Stated level | 6 dBm / 600 Ω | 6 dBm / 600 Ω | — |
| Gain, noise, distortion, clipping differences | UNKNOWN | UNKNOWN | UNKNOWN |

Same part types on both paths. Component values may differ; not established. For a stereo mix processor the main stereo output is the historically direct path. One PCM69A serves both main channels, so L and R share clock and reference (STRONGLY SUPPORTED).

---

## 21. MPC3000 sonic contribution ranking (line-level program at unity)

| Rank | Contributor | Evidence | Likely audibility | Hardware-fit need | MVP | Complexity |
|---|---|---|---|---|---|---|
| 1 | Gain structure and clipping at input / ADC full scale | VERIFIED sensitivity spec; clip point UNKNOWN | Audible only when driven | Yes | Boundary only | Low |
| 2 | 16-bit word-length reduction | VERIFIED storage; method UNKNOWN | Subtle; low-level only | Low-level tests | Yes (ideal quantizer) | Low |
| 3 | ADC decimation and DAC interpolation filters (band edge, ripple, pre-ringing, latency) | VERIFIED architecture; response UNKNOWN | Subtle near 20 kHz | Yes or datasheets | Placeholder | Low–medium |
| 4 | Analog input and output filters, coupling poles | VERIFIED existence; values UNKNOWN | Subtle (LF phase, HF droop) | Yes or schematic extraction | Placeholder | Low |
| 5 | Converter system linearity (AK5328, PCM69A low-level behavior) | Datasheet-class only | Probably inaudible | Yes | No | Medium |
| 6 | Op-amp nonlinearity (5532, M5220, M5238) | None | Probably inaudible below clip | Yes | No | Medium |
| 7 | Internal arithmetic (mixer scaling, rounding) | UNKNOWN | UNKNOWN | Yes | Identity placeholder | Low |
| 8 | Noise | UNKNOWN | UNKNOWN | Yes | Omit | Low |
| 9 | Interpolation | UNKNOWN; not active at unity pitch | None at unity | — | No | — |
| 10 | Clocking | Crystal master clock, synchronous dividers | None expected | Spectral check | No | — |
| 11 | Crosstalk | UNKNOWN | UNKNOWN | Stereo tests | No | — |
| 12 | Sample rate | 44.1 kHz | Transparent relative to SP-limited input | — | Yes | Low |

No entry above is supported as "likely audible" for an undriven line-level mix. This is the central open question for the MPC half (MPC3K-CLM-020).

---

## 22. Serial SP → MPC analysis

| Option | Historical defensibility | Mix-bus usefulness | Bandwidth | Noise | Aliasing / images | Latency | CPU | Gain staging | Measurability |
|---|---|---|---|---|---|---|---|---|---|
| 1. SP full record/playback → MPC full record/playback | Coherent as a physical chain (SP output sampled by MPC). No source gathered shows it was a standard practice (CHAIN-CLM-008, SPECULATIVE) | Dark and band-limited; strong effect | SP-limited (~13 kHz baseband) plus SP images up to 20 kHz admitted by MPC | Two quantizers; SP dominates by ~24 dB | SP images below 20 kHz pass through MPC intact | Required | Two rate domains | Needs both calibrations | Good: every stage is reachable by black-box tests |
| 2. SP converter/output coloration → MPC converter/output coloration | Abstraction; no input stages | Milder | Same | Same | Same | Required | Similar | Skips input clip boundaries, which are the most plausible nonlinearities | Good |
| 3. SP sample-domain → MPC analog/output only | Abstraction; omits MPC ADC | Close to option 1 if MPC ADC is transparent | Same | Lower | Same | Lower | Lower | Simple | MPC DAC+output is directly measurable via loaded samples |
| 4. Selectable layers | Product construct | Flexible | — | — | — | Varies | Higher | Complex | Each layer must be separately validated |
| 5. Reference superset (recommended for the *reference model*, not a product choice) | Option 1 structure with every block individually replaceable and bypassable, SP at unity pitch, MPC blocks as identity/linear placeholders until measured; "tuned round trip" as a separately labeled extreme mode | Derives options 1–4 by configuration | — | — | — | Required | Not a concern offline | Explicit | Best: one harness, block-level substitution |

Extreme-mode candidate (deferred, CHAIN-DEC-004): the documented 33⅓ → 45 rpm workflow. Ratio 33.33/45 = 0.7407 = −5.2 semitones, so the nearest machine tunings are −5 (0.7492) and −6 (0.7071) semitones with turntable pitch making up the difference. In the original time base this is equivalent to capturing at 26 041.67 × 0.7407 = 19 290 Hz (baseband 9.6 kHz) and replaying through the truncating table reader onto the 26 041.67 Hz hold grid. It is causal and needs no time-stretching. It is where the drop-sample character lives. It is unsuitable as a default mix-bus mode. The exact tuning table is UNKNOWN (P2).

---

## 23. Interstage calibration

| Quantity | Finding | Status |
|---|---|---|
| SP channel output nominal level | UNKNOWN | UNKNOWN |
| SP mix output nominal level | UNKNOWN (depends on MIX VOLUME) | UNKNOWN |
| SP full-scale output voltage | UNKNOWN | UNKNOWN |
| MPC input sensitivity | −18 / −38 / −58 dBs at maximum record level | VERIFIED |
| MPC input full-scale voltage per switch position and pot setting | UNKNOWN | UNKNOWN |
| Can the SP overdrive the MPC input? | Plausible for any line-level source because sensitivity is high; depends on pot position. Clip location UNKNOWN | PROVISIONAL |
| Impedance interaction | MPC Zin 45 kΩ. SP Zout UNKNOWN; unless unusually high, loading is negligible | PROVISIONAL |
| Is unity digital gain historically meaningful? | No. The connection was analog with a user-set record level; there was never a digital unity between the machines | STRONGLY SUPPORTED |
| Should an interstage trim exist? | Yes, as an explicit calibrated variable; it corresponds to MPC RECORD LEVEL. Default value cannot be set yet | CHAIN-DEC-014 |

**This is P0 research debt (RD-P0-03).** The conceptual connection is an analog voltage: SP full-scale sine in volts at the chosen output, and MPC volts-for-digital-full-scale at a stated switch and pot position. Both come from CHAIN-EXP-005 and -009.

---

## 24. Stereo / full-mix implications

| Question | SP-1200 | MPC3000 |
|---|---|---|
| Sampling mono? | Yes, one input | No, true stereo |
| Playback mono per voice? | Yes | Voices can be stereo sounds |
| True stereo sampling path? | No | Yes (one stereo ADC) |
| L/R output paths independent? | Channels are independent analog paths after a shared DAC; mix out is mono | Independent analog paths after one dual DAC |
| Clocks shared? | One clock; channels served in sequential 4.8 µs slots | One clock; co-phase DAC outputs |
| Filters matched? | Paired channels nominally identical (3–4, 5–6, 7–8); tolerance UNKNOWN | Nominally identical; tolerance UNKNOWN |
| Panning / summing coloration? | No pan; mono analog sum | Digital pan and mix; arithmetic UNKNOWN |

**Historically, the SP-1200 stage is mono.** A stereo mix could only have passed through it as two separately recorded mono samples played on two channels, with no sample-phase lock at capture (up to one sample period, 38.4 µs, of relative offset) and possibly a multiplex slot offset on playback (4.8 µs per slot = 17.3° at 10 kHz per slot; PROVISIONAL inference, CHAIN-EXP-007).

| Stereo abstraction | Assessment |
|---|---|
| Dual mono, independent clocks | Not historical; adds arbitrary inter-channel phase. Reject. |
| Linked dual mono (shared sampling instants, identical coefficients) | Product abstraction with the least invented behavior. Preserves image. **Adopted for the reference model** (CHAIN-DEC-005). |
| Shared clock, independent audio with slot skew | Closest to two SP channels playing two samples. Research configuration only, pending CHAIN-EXP-007. |
| Sum to mono | The only historically literal SP mix path (MIX OUT). Valid as a labeled mode; destroys width. |
| Mid/side | Creative abstraction only; never to be described as historical. |

No randomized channel mismatch (CHAIN-DEC-010).

---

## 25. Multirate architecture

Four rates are kept distinct:

| Rate | Value | Notes |
|---|---|---|
| Host rate | 44.1, 48, 88.2, 96, 176.4, 192 kHz | Outside the model |
| SP machine rate | 26 041.6667 Hz (PROVISIONAL constant 20 MHz / 768) | Sampling grid and hold grid |
| MPC machine rate | 44 100 Hz (VERIFIED) | Internally the ADC modulator runs at 64 fs and the DAC at 8 fs; these are inside the converter blocks |
| Analog-proxy / nonlinear oversampling rate | Implementation choice | Represents continuous-time signals between machines; must be high enough to carry SP hold images and to keep any static nonlinearity alias-free |

Exact ratios (given the provisional SP constant):

| Host rate | SP rate / host rate | MPC rate / host rate |
|---|---|---|
| 44 100 | 3125 / 5292 | 1 |
| 48 000 | 625 / 1152 | 147 / 160 |
| 88 200 | 3125 / 10 584 | 1 / 2 |
| 96 000 | 625 / 2304 | 147 / 320 |
| 176 400 | 3125 / 21 168 | 1 / 4 |
| 192 000 | 625 / 4608 | 147 / 640 |

Invariance requirement: the machine-domain sample sequence must be a function of the continuous-time input only. Host rate changes only what the host can represent of the output (content above host Nyquist is band-limited away, as an interface recording the hardware would do). At a 44.1 kHz host, SP images above 22.05 kHz are simply not representable; this is a host limit, not model behavior.

Hardware sample-rate conversion (the machines' own sampling) is model behavior. Oversampling used to keep numerical aliasing out of analog-stage models is implementation and must be inaudible by construction.

---

## 26. Gain staging and clipping boundaries

Stages: input trim → SP input level (preamp gain 0/+20/+40 dB) → SP converter limit → SP output level → interstage → MPC input level (switch + pot) → MPC converter limit → MPC output level → final output.

| Overload point | Nominal level | Clip onset | Hard / soft | Symmetry | Frequency dependence | Recovery | Channel dependence | Status |
|---|---|---|---|---|---|---|---|---|
| SP analog input (preamp, AA filter op-amps) | UNKNOWN | UNKNOWN | Op-amp rail clipping is hard; not confirmed to occur before the ADC limit | UNKNOWN | Filter peaking could shift it; UNKNOWN | UNKNOWN | Mono | UNKNOWN |
| SP ADC | FS voltage UNKNOWN | Code range 0…4095 | Hard clamp presumed | Depends on bias/offset trim; UNKNOWN | None | Immediate presumed | Mono | PROVISIONAL |
| SP digital domain | — | No digital gain stage at unity | — | — | — | — | — | PROVISIONAL |
| SP DAC / output | UNKNOWN | Cannot exceed DAC full scale; output amp clip UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Per channel | UNKNOWN |
| MPC analog input | Sensitivity −18/−38/−58 dBs | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | L/R | UNKNOWN |
| MPC ADC | FS UNKNOWN | Digital full scale | Delta-sigma modulators overload before or at FS and may recover non-instantly; AK5328 behavior UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | L/R | UNKNOWN |
| MPC internal mixer | — | UNKNOWN scaling | UNKNOWN (saturating or wrapping) | — | — | — | — | UNKNOWN |
| MPC DAC / output | "6 dBm" nominal as printed | Digital FS; analog stage clip above that presumed | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | L/R | UNKNOWN |

Three kinds of clipping are kept separate in the model: analog (stage-specific, level in volts), converter (code range), digital (arithmetic). Every clamp is explicit and calibrated; floating-point overflow is never the clipping mechanism.

Mechanism classification:

| Mechanism | Class | Depends on |
|---|---|---|
| SP AA filter, channel filters, coupling networks | STATIC LINEAR | FREQUENCY |
| SP sample-and-hold sampling | ALIASING | FREQUENCY, SAMPLE RATE |
| SP 12-bit quantizer | QUANTIZATION | LEVEL |
| SP ADC clamp | STATIC NONLINEAR | LEVEL |
| SP zero-order hold | STATIC LINEAR (plus images) | FREQUENCY, SAMPLE RATE |
| SP tuned playback (extreme mode) | ALIASING, STATEFUL (phase accumulator) | FREQUENCY, TIME, SAMPLE RATE |
| SP SSM2044 channels | DYNAMIC NONLINEAR, STATEFUL | LEVEL, FREQUENCY, TIME (excluded) |
| MPC input stages | STATIC LINEAR until clip | FREQUENCY, LEVEL |
| MPC ADC / DAC digital filters | STATIC LINEAR | FREQUENCY |
| MPC 16-bit word reduction | QUANTIZATION | LEVEL |
| MPC ADC overload | DYNAMIC NONLINEAR possible | LEVEL, TIME |
| Any analog noise | NOISE | CHANNEL; level-independent unless shown |
| Load interaction | None expected | LOAD (PROVISIONAL negligible) |

Drive question (no control is defined): a future "drive" could mean SP input level, calibration offset, interstage level, MPC input level, output level, or a nonlinearity macro. Only the first, third and fourth correspond to physical controls on the machines (SP gain setting plus source level; MPC record level and switch). A macro that moves several of these at once would not map to one model variable and is not recommended (CHAIN-DEC-012).

---

## 27. Noise / clock / power

**Noise policy.** No noise is added because the hardware is old.

| Component | Evidence | Class | Default |
|---|---|---|---|
| SP quantization error | Produced by the quantizer itself | ESSENTIAL (not "added noise") | Inherent |
| SP idle analog noise, hum | None | UNKNOWN | OMITTED |
| SP multiplex / clock feedthrough at 26.04 kHz and 208.33 kHz | Plausible; SRC-04 saw a tone at 26 kHz on an SP-12 | UNKNOWN magnitude; above the band of most hosts | OMITTED |
| SP power-supply spurs | None | UNKNOWN | OMITTED |
| MPC quantization error (16-bit) | Inherent | ESSENTIAL but ≈ −98 dB | Inherent |
| MPC converter and amplifier noise | Datasheet-class only | NEGLIGIBLE expected, UNKNOWN installed | OMITTED |
| Channel correlation of noise | None | UNKNOWN | — |
| Vinyl noise, tape hiss | Not part of either machine | — | REJECTED |

**Clock.** SP-1200: crystal oscillator (20 MHz PROVISIONAL) with synchronous division; record and playback share it; pitch never changes the clock. MPC3000: 33.8688 MHz crystal, 768 fs, synchronous dividers. Likely jitter magnitude: UNKNOWN, expected small for crystal sources. No measured spectral effect supports modeling jitter. Randomized sample jitter is rejected (CHAIN-DEC-008). The only clock-related behaviors with support are deterministic: the fixed 26.04 kHz grid, and the truncating phase accumulator in tuned playback.

**Power supply.** MPC3000: linear regulators NJM7812FA / NJM7912FA (±12 V), 5 V regulators and LM2940 LDOs local to converters; VERIFIED parts. SP-1200: original supply ran hot and was redesigned for the 1993 reissue (SRC-06); rail values UNKNOWN. With regulated rails and line-level loads, sag and supply modulation are not plausible audible mechanisms. Ripple spurs are UNKNOWN and would appear in the idle spectrum (CHAIN-EXP-006). Power-supply modeling is rejected (CHAIN-DEC-009).

**Component tolerance.** Unit variation in filter corners is certain to exist and UNKNOWN in size. Classification: product REJECT (no randomization), research DEFER (optional variation study if a second unit is ever measured).

---

## 28. Candidate reference architecture

Unsupported blocks from the brief's example are removed: there is no SP "VCA" block, no SP digital mixer, and no MPC nonlinearity block. Placeholders are named as placeholders.

| # | Block | Rate | States | Nonlinearity | Latency | Evidence | Replaceable by | Test |
|---|---|---|---|---|---|---|---|---|
| R0 | Input calibration (dBFS → volts) | Host | None | None | 0 | Decision | Measured calibration | EXP-005 |
| R1 | Host → analog-proxy resampler | Host → proxy | FIR | None | Filter delay | Implementation | — | EXP-016 |
| R2 | SP input gain (0/+20/+40 dB) with explicit analog clamp | Proxy | None | Placeholder clamp, level UNSET | 0 | Gain STRONGLY SUPPORTED; clamp UNKNOWN | Measured gain curve | EXP-002, -005 |
| R3 | SP anti-alias filter | Proxy | IIR | None | Group delay | PLACEHOLDER coefficients | SPICE-derived or measured response | EXP-019, -002 |
| R4 | SP sampler (ideal sample-and-hold) | Proxy → 26 041.67 Hz | None | Aliasing (historical) | ≤ 1 SP sample | STRONGLY SUPPORTED | Aperture model if measured | EXP-001, -002 |
| R5 | SP 12-bit quantizer with code clamp | SP | None | Quantization, hard clamp | 0 | VERIFIED word length; rounding rule PLACEHOLDER | Measured transfer | EXP-002 |
| R6 | SP machine domain | SP | None at unity | None | 0 | Identity at unity PROVISIONAL | Tuned-playback block (extreme mode) | EXP-003 |
| R7 | SP DAC + zero-order hold | SP → proxy | Hold | None (images are linear) | ½ SP sample | VERIFIED hold; full-period PROVISIONAL | Measured hold fraction | EXP-003 |
| R8 | SP output filter, selected: none / ch 5–6 / ch 3–4 | Proxy | IIR | None | Group delay | PLACEHOLDER coefficients | SPICE or measurement | EXP-019, -004 |
| R9 | SP output stage (gain, coupling pole) | Proxy | 1 pole | None | ~0 | PLACEHOLDER | Measurement | EXP-004, -005 |
| R10 | Interstage calibrated gain | Proxy | None | None | 0 | UNSET (P0) | Measured levels | EXP-005, -009, -012 |
| R11 | MPC input stage (switch, record level, coupling pole) with explicit clamp | Proxy | 1 pole | Placeholder clamp, UNSET | ~0 | Sensitivity VERIFIED; rest PLACEHOLDER | Extraction or measurement | EXP-009, -020 |
| R12 | MPC ADC: decimation to 44.1 kHz, full-scale clamp, 18-bit | Proxy → 44.1 kHz | FIR | Clamp | Filter delay | Architecture VERIFIED; response PLACEHOLDER | Datasheet response, measured overload | EXP-009 |
| R13 | MPC word-length reduction 18 → 16 bit | 44.1 kHz | None | Quantization | 0 | Method UNKNOWN; research switch truncation / rounding | Result of low-level test | EXP-008 |
| R14 | MPC machine domain | 44.1 kHz | None | None | 0 | Identity PLACEHOLDER | Measured arithmetic | EXP-008, -010 |
| R15 | MPC DAC: 8× interpolation, 18-bit, I/V, analog low-pass, coupling pole | 44.1 kHz → proxy | FIR + IIR | None | Filter delay | Architecture VERIFIED; responses PLACEHOLDER | Datasheet, extraction, measurement | EXP-010, -020 |
| R16 | Analog-proxy → host resampler, output trim | Proxy → host | FIR | None | Filter delay | Implementation | — | EXP-016 |

Diagnostic taps are required after every block. Each machine can be bypassed as a whole (section 43 notes bypass semantics).

---

## 29. Modeling strategy

**Converters (options A–F from the brief).**

| Converter | Recommended now | Rationale | Upgrade trigger |
|---|---|---|---|
| SP ADC | A + C: ideal 12-bit quantizer with clamp, plus the AA filter and sampler | Word length and architecture are supported; no transfer data exists | B (measured transfer error) only if EXP-002 shows residual not explained by ideal quantization |
| SP DAC | A + C: ideal 12-bit values, zero-order hold, output filter | Hold is verified; INL may cancel against the ADC | B if EXP-003 shows otherwise. D (component-derived) is F: unnecessary |
| MPC ADC | C: linear decimation response + clamp + 18-bit quantizer | Delta-sigma internals are not identifiable from outside | E (black-box residual) only if EXP-009 finds level-dependent residual above the noise floor |
| MPC DAC | C: interpolation response + analog filter | PCM69A capability exceeds 16-bit data | E only on evidence |
| INL/DNL, glitch, settling, reference behavior, zero-crossing | F for both machines today | No evidence; poorly identifiable | Measured evidence |

**Analog blocks (L0–L4).**

| Block | Recommended level | Method | Identifiability |
|---|---|---|---|
| SP preamp | L0 + explicit clamp | Gain constant; clamp from measured gain curve | Good from stepped-level measurement |
| SP AA filter | L0 | Linear IIR from SPICE AC analysis of extracted schematic (the SRC-04 method), cross-checked by measurement | Good |
| SP channel filters 3–6 | L0 | Same | Good |
| SP SSM2044 channels | Out of scope | — | — |
| SP mix amp | L0 | Gain + coupling pole | Good |
| MPC input chain | L0 + explicit clamp | Linear + measured clip point | Good |
| MPC I/V and output filter | L0 | Linear IIR | Good |
| Any L1–L4 nonlinear block | Not recommended | No evidence of nonlinearity below clip | A Wiener or Hammerstein fit without measured harmonics would be POORLY IDENTIFIABLE and unvalidatable |

Lowest complexity that reproduces the evidence is linear filters, two quantizers, a sampler, a hold, and explicit clamps. Nothing more is justified today.

**Aliasing policy.**

| Alias / image source | Classification |
|---|---|
| SP sampling of content above 13.02 kHz that passes the AA filter | HISTORICAL |
| SP hold images above 13.02 kHz | HISTORICAL |
| SP drop-sample tuning products | HISTORICAL (extreme mode only) |
| MPC ADC fold-back in the 22.05–24 kHz transition band | HISTORICAL, expected negligible |
| Aliasing from resamplers R1/R16 | IMPLEMENTATION; must be below the model's own floor |
| Aliasing from clamps evaluated at too low a rate | IMPLEMENTATION; not authentic |

**Phase, transient, LF and HF behavior.** Magnitude-only modeling is not acceptable. Group delay near the SP band edge depends on the AA and channel filter orders (UNKNOWN); steep analog low-pass filters ring at their corner on transients, which is a candidate measurable mechanism behind informal "punch" or "smear" descriptions (SPECULATIVE until an impulse response exists). The hold is linear phase (half-sample delay). MPC digital filters are FIR and presumably linear phase with pre-ringing near 20–22 kHz (PROVISIONAL). Coupling poles in both machines set LF phase; sustained sub-bass in a finished mix makes these worth measuring even if drums never revealed them (EXP-004, -010 with 10 Hz – 200 Hz detail). HF behavior is the combination of AA response, fold-back, hold droop, images and channel filter, never a single low-pass cutoff.

**Intermodulation.** With no supported static nonlinearity below clip, expected IMD is that of quantization and aliasing: for the SP, difference and fold-back products of dense HF content are deterministic consequences of sampling and are reproduced by the skeleton. Any nonlinear block added later must match SMPTE, CCIF and multitone results, not only THD.

---

## 30. Hardware measurement plan

Assumes one stock SP-1200 and one stock MPC3000.

| Item | Specification |
|---|---|
| Interface | 192 kHz / 24-bit capture and playback; line I/O with known calibration; loopback THD+N at least 20 dB better than the best figure to be measured; response known to 80 kHz; S/PDIF output at 44.1 kHz for MPC digital input |
| Calibration | Interface loopback captured at the start and end of every session; absolute level calibrated with a true-RMS meter at 1 kHz (volts per dBFS for input and output) |
| Cables | Short unbalanced TS to the machines; a TRS breakout for SP filtered/unfiltered contacts with each contact captured separately; lengths and types recorded |
| Clocking | Interface on internal clock. Machines free-run. Clock ratio estimated from pilot tones at the start and end of every capture |
| Warm-up | Power on time and ambient temperature logged; captures begin only after a logged warm-up interval. THRESHOLD NOT YET DEFINED (derive from drift observed in repeated captures) |
| Capture rate | 192 kHz for everything analog, so SP images and clock spurs to 96 kHz are recorded |
| I/O selection | SP: each of ch 3, 5, 7 filtered and unfiltered contacts, and MIX OUT. MPC: main L/R, one individual pair, each input gain position |
| Levels | Stepped from −60 dB to above clip re each machine's measured full scale |
| Repeat count | 3 per configuration, to estimate repeatability (not a pass criterion) |
| Metadata | Unit ID, serial, revision, modification status, OS/firmware, warm-up, interface, calibration values, cables, I/O used, switch and pot positions (pot positions photographed), levels, sample rate |
| File naming | `{machine}_{unit}_{category}_{signal}_{path}_{level}_{take}.wav`, with a sidecar JSON |
| Checksums | SHA-256 for every stimulus and capture, stored in the sidecar and in a manifest |

**Measurement signals.**

| Signal | Rate / depth | Peak | Duration | Channels |
|---|---|---|---|---|
| Log sweep 10 Hz – 90 kHz | 192 k / 24 | −20, −10, −3 dB re machine FS | 10 s (SP: ≤ 2.3 s segments, see note) | Mono; L-only, R-only for MPC |
| Stepped sine 20 Hz – 20 kHz, 1/6 octave | 192 k / 24 | −60 … +6 dB re FS in 3 dB steps at 100 Hz, 1 kHz, 10 kHz | 1 s per step | Mono / each channel |
| 100 Hz, 1 kHz, 10 kHz sines | 192 k / 24 | −1 dB re FS | 2 s | Mono / stereo |
| SMPTE IMD 60 Hz + 7 kHz 4:1 | 192 k / 24 | −3, −10 dB | 2 s | Mono / stereo |
| CCIF IMD 19 + 20 kHz (MPC); 10 + 11 kHz (SP, in band) | 192 k / 24 | −3, −10 dB | 2 s | Mono / stereo |
| Multitone, 31 tones log-spaced, random phase, seeded | 192 k / 24 | −12 dB crest-normalized | 2 s | Mono / stereo |
| Music-like multitone (pink-weighted) | 192 k / 24 | −12 dB | 2 s | Stereo |
| Impulse, band-limited to 80 kHz | 192 k / 24 | −6 dB | 0.5 s | Mono / each channel |
| Square 100 Hz and 1 kHz; single pulse | 192 k / 24 | −6 dB | 1 s | Mono |
| Silence | — | — | 2 s | — |
| Low-level sine 1 kHz | 192 k / 24 | −60, −70, −80 dB re FS | 2 s | Mono |
| White noise, pink noise (seeded) | 192 k / 24 | −12 dB RMS-normalized | 2 s | Mono; correlated, uncorrelated, anti-phase stereo for MPC |
| Slow ramp across full code range | 192 k / 24 (analog) and synthetic sample data (digital) | Full scale | 2 s | Mono |
| Transient drum loop, bass-heavy mix, bright mix, dense master, dynamic premaster | 192 k / 24 source | As mastered and −12 dB | SP: 2.3 s excerpts; MPC: up to 10 s stereo with standard memory | Mono (SP), stereo (MPC) |

Note: the SP-1200 can only pass audio by recording it, and one sound is limited to 2.5 s. Every SP stimulus is therefore a ≤ 2.3 s segment with pilot tones. A full mix cannot be streamed through the hardware.

**Measurement categories:** LINEAR (frequency, phase, group delay, channel matching, crosstalk); LEVEL (gain curve, clip onset, output ceiling, overload recovery); DISTORTION (THD vs level and frequency, harmonic balance, SMPTE, CCIF, multitone); NOISE (idle spectrum, loaded noise, DC, hum, spurs); DIGITAL (quantizer transfer, low-level behavior, images, aliasing, truncation vs rounding); TRANSIENT (impulse, square, recovery); STEREO (L-only, R-only, dual mono, correlated, anti-phase).

**Black-box differential tests.** Both machines expose their digital sample data, which makes clean isolation possible without opening them.

| Target | Method |
|---|---|
| SP analog input + AA + ADC | Record stimuli, then export the sample data (disk image or MIDI sample dump) and analyze the 12-bit words directly |
| SP DAC + hold + output path | Load synthetic 12-bit sample data (ramps, impulses, sines, full-scale codes) and capture each output |
| SP full machine | Record and play back; must equal the composition of the two above (consistency check) |
| SP main vs individual, filtered vs unfiltered | Same sample, every output and contact; ratios give each filter's response directly |
| MPC analog input + ADC | Sample via analog input, save sound to disk, analyze the 16-bit file |
| MPC storage transparency | Sample via S/PDIF, save, compare with the source bits |
| MPC DAC + output | Load synthetic 16-bit sounds from disk and capture main and individual outputs |
| MPC full machine | Analog in to analog out; must equal the composition |
| MPC input stage vs ADC | Difference between analog-in and S/PDIF-in captures of the same program |

---

## 31. Hardware fitting

| Block | Stimulus | Capture | Preprocessing | Fit parameters | Objective | Validation metric | Overfitting risk |
|---|---|---|---|---|---|---|---|
| SP AA filter | Sweep, multitone (FIT); impulse, noise (VALIDATION) | Exported sample data | Clock-ratio estimate, alignment | Pole/zero set constrained to the schematic's topology and order | Complex response error | Response error on validation captures; fold-back profile | Low if order is fixed by schematic |
| SP quantizer | Slow ramp (FIT); low-level sines (VALIDATION) | Exported sample data | Histogram, code transitions | Offset, rounding rule, clamp codes | Code-transition match | Low-level harmonic profile | Low |
| SP hold + output filter | Synthetic impulses and sines (FIT); noise, music excerpts (VALIDATION) | 192 kHz analog | Alignment, gain | Hold fraction; pole/zero set per output | Complex response error to 96 kHz | Image levels; null residual on excerpts | Low to medium |
| SP levels and clamp | Stepped sine | Both | — | Volts per FS; clip threshold | Gain-curve match | Clip onset on a different frequency | Low |
| MPC input chain | As SP AA | Saved 16-bit files | Alignment | Gain per switch, poles, clamp | Response and gain-curve error | Validation captures | Low |
| MPC ADC / DAC filters | Sweep, impulse | Saved files; 192 kHz analog | Alignment | FIR response (or datasheet coefficients) | Response error | Pre/post-ringing shape on impulse | Low |
| MPC word-length reduction | Low-level sines with and without dither | Saved files | — | Rule selection (discrete) | Exact bit match where possible | Bit match on other signals | None (discrete) |
| Any nonlinear residual | Stepped sine (FIT); SMPTE, CCIF, multitone (VALIDATION) | 192 kHz | Null against linear model | Lowest-order model that explains residual | Harmonic residual | IMD residual | High; require IMD validation |

FIT and VALIDATION sets are disjoint captures. No free equalizer or per-file gain is allowed in validation beyond the single calibration gain and the clock-ratio and delay alignment.

---

## 32. Validation plan

**Null / difference framework.**

| Step | Definition |
|---|---|
| Sample-rate normalization | Both signals at 192 kHz (hardware capture rate); model rendered at the same rate |
| Clock-drift correction | Ratio from pilot tones at both ends; one constant ratio per capture; no time-varying warping |
| Latency alignment | Sub-sample delay from cross-correlation of the pilot segment only |
| Gain alignment | One broadband scalar from the 1 kHz calibration tone; never from the program material |
| Polarity | Determined once per path from the impulse; fixed thereafter |
| DC | Reported, then removed identically from both signals with a documented high-pass |
| Reported | Residual peak dBFS, residual RMS dB re signal RMS, residual spectrum, correlation coefficient, per-band residual |
| Prohibited | Any EQ, dynamic gain, or fitted filter applied to either signal to improve the null |

**Acceptance metrics (definitions only).**

| Metric | Definition | Threshold |
|---|---|---|
| Frequency response error | Max and RMS dB deviation, 20 Hz – band edge, 1/12 octave | THRESHOLD NOT YET DEFINED |
| Phase error | Degrees after removal of pure delay | THRESHOLD NOT YET DEFINED |
| Group delay error | ms vs frequency | THRESHOLD NOT YET DEFINED |
| Harmonic residual | Per-harmonic level difference vs level and frequency | THRESHOLD NOT YET DEFINED |
| IMD residual | SMPTE, CCIF and multitone product level differences | THRESHOLD NOT YET DEFINED |
| Alias / image profile | Level and frequency of each fold-back and image component | THRESHOLD NOT YET DEFINED |
| Quantization transfer | Code-transition agreement (SP: exact match is achievable on exported data and should be the target) | Exact match where data is digital; otherwise NOT YET DEFINED |
| Null residual | RMS dB re signal, per material class | THRESHOLD NOT YET DEFINED |
| Stereo correlation | Difference in inter-channel correlation, model vs hardware | THRESHOLD NOT YET DEFINED |
| Peak / RMS / crest factor change | dB differences | THRESHOLD NOT YET DEFINED |

Principle for setting thresholds later: the hardware-versus-hardware residual across the three repeat captures is the floor. A model cannot be required to null better than the unit nulls against itself. Thresholds will be set relative to that floor once it is measured.

**Order experiment and level-matched cascade tests.** DRY, SP only, MPC only, SP→MPC, MPC→SP, output-level matched (matched by RMS over the full excerpt with the matching gain reported), on full mix, drums, bass-heavy and bright material; metrics: frequency, phase, THD, IMD, noise, crest factor, stereo correlation, residual spectrum. Expected asymmetry (hypothesis only): MPC→SP removes everything above ~13 kHz last and leaves SP images unfiltered at the output, whereas SP→MPC passes the same images through a transparent stage, so the two orders may differ little unless the MPC input is driven. NOT EXECUTED. Reverse order is not added to the product on the basis of this document (CHAIN-DEC-013).

**Full-mix viability (ANALYSIS from verified mechanisms; not measured).**

| Material | SP stage (unity, unfiltered output) | SP stage (channel 3–4 filter) | MPC stage | Cascade verdict |
|---|---|---|---|---|
| Dense mastered | Top octave lost; images add inharmonic HF; quantization masked | Darker, images reduced | No expected change unless input clipped | Usable as a strong color; needs explicit headroom |
| Dynamic premaster | Quantization error audible in quiet passages and tails | Same | None expected | Usable; low-level behavior is the risk |
| Sub-heavy | Depends on unknown coupling poles and input headroom | Same | Depends on coupling poles | UNKNOWN until LF measured |
| Bright mix | Fold-back from 13–15 kHz and strong images; most altered case | Reduced | None expected | Likely the most audible and most polarizing |
| Wide stereo | Preserved only under the linked dual-mono abstraction; mono under literal MIX OUT | Same | Preserved | Abstraction-dependent |
| Clipped modern mix | Flat-topped waveforms contain HF that aliases; hard edges ring through the AA filter | Same | Inter-sample peaks may exceed FS at MPC ADC | Needs inter-sample-aware headroom |
| Quiet mix | Quantization error correlated with signal; granular | Same | None expected | Level calibration decides everything |

Tuned round-trip mode is rejected for normal mix-bus use on bandwidth and aliasing grounds and survives only as a clearly labeled extreme mode candidate.

---

## 33. Listening-test plan

Blocked until measurable models exist (CHAIN-EXP-018, NOT EXECUTED). No listening results are claimed anywhere in this document.

- Conditions: HARDWARE capture, REFERENCE MODEL, SIMPLIFIED MODEL, BYPASS.
- Level matching by RMS over each excerpt, matching gains logged; no loudness normalization inside the models.
- Blind labels, randomized order per trial, ABX or MUSHRA-style with hidden reference; trial logs retained.
- Material: full mix, drums, bass, bright mix, dense master, dynamic premaster. For SP comparisons every excerpt is ≤ 2.3 s because of the hardware limit, which constrains test design.
- Stimuli labeled LISTENING STIMULUS under the artifact policy; hardware captures and model renders never share a filename pattern.

Audibility classification of candidate behaviors (predictions, not results):

| Behavior | Class |
|---|---|
| SP band limit and images | MEASURABLE AND LIKELY AUDIBLE (measured on SP-12 in SRC-04; not yet on our unit) |
| SP quantization at low level | MEASURABLE AND LIKELY AUDIBLE on quiet material; LIKELY SUBTLE on dense material |
| SP hold droop | MEASURABLE BUT LIKELY SUBTLE |
| SP converter static error | NOT YET MEASURED; expected PROBABLY INAUDIBLE |
| SP analog nonlinearity below clip | NOT YET MEASURED |
| MPC band-edge filters, 16-bit reduction | MEASURABLE AND PROBABLY INAUDIBLE to SUBTLE |
| MPC analog nonlinearity below clip | NOT YET MEASURED |
| MPC input overload | NOT YET MEASURED; likely audible when driven |
| Noise, jitter, supply effects | NOT YET MEASURED / UNKNOWN |

Complexity is not implemented solely because something can be measured.

---

## 34. Claim ledger

Confidence: H / M / L. "Test" refers to section 36.

### SP-1200

| ID | Subsystem | Claim | Evidence / source | Status | Conf. | Implementation impact | Hardware test |
|---|---|---|---|---|---|---|---|
| SP12-CLM-001 | Clock | Sample rate is nominally 26.04 kHz for record and playback | SRC-05; ~26 kHz tone measured on SP-12, SRC-04 | VERIFIED | H | Defines SP machine rate | EXP-001 |
| SP12-CLM-002 | Clock | Rate derives from 20 MHz ÷ 3 ÷ 256 = 26 041.67 Hz | SRC-10 | PROVISIONAL | M | Exact constant and rate ratios | EXP-001, -019 |
| SP12-CLM-003 | Format | Data format is 12-bit linear | SRC-05 | VERIFIED | H | Quantizer word length | EXP-002 |
| SP12-CLM-004 | ADC | Conversion is successive approximation using SAR logic, a comparator and the playback DAC, after a sample-and-hold | SRC-04 (SP-12), SRC-09, SRC-10 | STRONGLY SUPPORTED | M–H | No separate ADC model; ADC and DAC share one transfer | EXP-002, -019 |
| SP12-CLM-005 | DAC | The DAC is an AD7541 12-bit multiplying DAC | SRC-11, SRC-08 | STRONGLY SUPPORTED | M–H | Datasheet to consult | EXP-019 |
| SP12-CLM-006 | Output | One DAC is time-multiplexed to 8 channels, each with its own hold | SRC-09, SRC-10 | STRONGLY SUPPORTED | M–H | Hold model; slot timing | EXP-007 |
| SP12-CLM-007 | Level | Per-voice level is set by an 8-bit multiplying DAC referenced to the 12-bit DAC output | SRC-09 | PROVISIONAL | L–M | No digital gain block; unity point unknown | EXP-003 |
| SP12-CLM-008 | Input | AA filter is a fixed multi-section active low-pass on TL084 op-amps; on the SP-12 it attenuates above ~15 kHz | SRC-04, -09, -12 | STRONGLY SUPPORTED (topology class); PROVISIONAL (corner) | M | Linear filter block; fold-back band | EXP-002, -019 |
| SP12-CLM-009 | Aliasing | On the SP-12, aliasing from input sampling is a minor contributor; output imaging and tuning dominate | SRC-04 | LITERATURE-DERIVED | M | Priority ranking | EXP-002, -004 |
| SP12-CLM-010 | Playback | Pitch change is by dropping/repeating samples with a truncated fractional index at fixed output rate | SRC-05, -06, -04 | VERIFIED | H | Unity is identity; tuned mode is a separate block | EXP-003 |
| SP12-CLM-011 | Playback | Tuning is in semitone steps | SRC-04 (SP-12) | LITERATURE-DERIVED | M | Extreme-mode ratios | — |
| SP12-CLM-012 | Output | Channels 7–8 have no filter; hold images appear above 13 kHz | SRC-03, -05; measured on SP-12 in SRC-04 | VERIFIED | H | ZOH + no filter option | EXP-004 |
| SP12-CLM-013 | Output | Channels 1–2 use SSM2044 4-pole filters whose cutoff is swept by an envelope started at trigger, fixed Q | SRC-03, -05, -04 | VERIFIED (existence); LITERATURE-DERIVED (sweep) | H | Excluded from MVP | — |
| SP12-CLM-014 | Output | Channels 3–4 have a fixed low-pass at a lower corner than channels 5–6 | SRC-05 | VERIFIED | H | Two selectable filter blocks; values unknown | EXP-004, -019 |
| SP12-CLM-015 | Output | MIX OUT is a mono mix of the eight channel outputs with a volume control | SRC-03 | VERIFIED | H | Mono-sum mode; summing topology unknown | EXP-004 |
| SP12-CLM-016 | Output | Unfiltered versions of channel outputs are available at the individual jacks on an alternate contact | SRC-03, -06 | VERIFIED (existence) | H | Direct measurement of each filter by ratio | EXP-004 |
| SP12-CLM-017 | Input | Sampling is mono through a single input | SRC-13; single jack | STRONGLY SUPPORTED | H | SP stage has no historical stereo | — |
| SP12-CLM-018 | Input | Input gain is selectable 0 / +20 / +40 dB | SRC-13 (multiple owners) | STRONGLY SUPPORTED | M | Gain variable | EXP-005 |
| SP12-CLM-019 | Quantization | An ideal 12-bit quantizer has 74.0 dB SQNR; LSB is −72.2 dB re FS | Arithmetic; SRC-04 uses 72 dB | SIMULATED (statement about the ideal model) | H | Expected floor | EXP-002 |
| SP12-CLM-020 | Output | An ideal full-period hold at 26 041.67 Hz has −0.53 / −2.22 / −3.92 dB at 5 / 10 / 13.02 kHz | Arithmetic | SIMULATED | H | Expected droop if hold is full-period | EXP-003 |
| SP12-CLM-021 | Analog | Input and output filters use TL084 op-amps | SRC-11, -12 | STRONGLY SUPPORTED | M | Device class only | EXP-019 |
| SP12-CLM-022 | Workflow | 2.5 s per sound, 10 s total | SRC-05, -06 | VERIFIED | H | Not modeled; constrains hardware tests | — |
| SP12-CLM-023 | Levels | Nominal levels, impedances, rails and clip points | None | UNKNOWN | — | Blocks calibration | EXP-005 |
| SP12-CLM-024 | ADC | Presence of dither, rounding rule, encoding | None | UNKNOWN | — | Quantizer placeholder | EXP-002 |
| SP12-CLM-025 | Revisions | 1993 reissue changed power supply and chassis; SSM2044 used until 1998; 2021 Rossum reissue keeps the format, substitutes SSI2144, adds input monitor and separate filtered/unfiltered jacks | SRC-05, -06, -14 | VERIFIED | H | Revision table | — |
| SP12-CLM-026 | Converter | Static DAC nonlinearity largely cancels between record and playback because one DAC serves both | Own inference | SPECULATIVE | L | Could make INL modeling unnecessary | EXP-002, -003 |

### MPC3000

| ID | Subsystem | Claim | Evidence / source | Status | Conf. | Implementation impact | Hardware test |
|---|---|---|---|---|---|---|---|
| MPC3K-CLM-001 | Format | 44.1 kHz sampling; stated response 20 Hz – 20 kHz | SRC-20 | VERIFIED | H | MPC machine rate | EXP-009, -010 |
| MPC3K-CLM-002 | Format | Storage is 16-bit linear | SRC-20, -24, -26 | VERIFIED | H | 16-bit quantizer | EXP-008 |
| MPC3K-CLM-003 | ADC | AK5328-VP, 18-bit stereo delta-sigma with 64 fs oversampling digital filter | SRC-20, -21, -27 | VERIFIED | H | Decimation-filter block | EXP-009 |
| MPC3K-CLM-004 | DAC main | SM5841HP 8× digital filter feeding PCM69AP 18-bit dual DAC | SRC-20, -21 | VERIFIED | H | Interpolation + DAC block | EXP-010 |
| MPC3K-CLM-005 | DAC individual | Four SM5841HP + four PCM69AP, NJM5532D I/V, M5220L filter/buffer, to eight 2-pole jacks | SRC-20, -21 | VERIFIED | H | Same block reused | EXP-011 |
| MPC3K-CLM-006 | Output main | PCM69A → NJM5532D → M5220L low-pass/buffers → relay → stereo out; M5216L for phones | SRC-20 block diagram | STRONGLY SUPPORTED | M–H | Linear output block | EXP-010, -020 |
| MPC3K-CLM-007 | Input | 3-pole jacks, 45 kΩ; sensitivity −58 / −38 / −18 dBs; 3-position switch; dual 10 kΩ record-level pot; M5238AL, M5220L, µPC812C | SRC-20 | VERIFIED (parts, spec); PARTIAL (topology) | H | Input gain variables | EXP-009, -020 |
| MPC3K-CLM-008 | Power | Regulated ±12 V; local 5 V regulators and LDOs at converters | SRC-20 parts list | VERIFIED (parts); PROVISIONAL (assignment) | M | No supply modeling | — |
| MPC3K-CLM-009 | Clock | 33.8688 MHz crystal = 768 × 44.1 kHz; synchronous | SRC-20 | VERIFIED | H | No jitter model | — |
| MPC3K-CLM-010 | DSP | Akai L7A1045 L6028 "18 bit digital signal processor" with serial 18-bit DAC data and separate word clocks per output pair | SRC-20 IC information | VERIFIED | H | Output word length is 18 bits | EXP-008, -010 |
| MPC3K-CLM-011 | Filter | Per-voice 12 dB/oct resonant low-pass is digital | SRC-20 spec; no analog VCF parts | STRONGLY SUPPORTED | H | Not in mix path at unity | — |
| MPC3K-CLM-012 | Stereo | True phase-locked stereo sampling | SRC-24; stereo ADC | VERIFIED | H | Stereo is historical here | — |
| MPC3K-CLM-013 | Digital in | S/PDIF input via YM3623B, 44.1 kHz only | SRC-20, -25 | VERIFIED | H | Enables differential tests | EXP-008 |
| MPC3K-CLM-014 | Levels | Stereo and individual output level printed as "6 dBm / 600 ohms" | SRC-20 (OCR; sign not legible) | VERIFIED text; PROVISIONAL meaning | M | Output calibration | EXP-010 |
| MPC3K-CLM-015 | DAC | PCM69A: 10-bit DAC + 1-bit first-order noise-shaped DAC, single +5 V, 0–1.2 mA, 1.8 kΩ, DR 106 dB, max THD+N −92 dB, SNR 110 dB | SRC-22, -23 | VERIFIED (datasheet capability) | H | DAC not the limiting element on paper | EXP-010 |
| MPC3K-CLM-016 | Digital | Method of 18 → 16-bit reduction | None | UNKNOWN | — | Research switch | EXP-008 |
| MPC3K-CLM-017 | Digital | Mixer word length, gain/pan arithmetic, interpolation | None | UNKNOWN | — | Identity placeholder | EXP-008, -010 |
| MPC3K-CLM-018 | Analog | Input and output filter orders and corners | Values present in SRC-20 scan; not extracted | UNKNOWN | — | Placeholder filters | EXP-020 |
| MPC3K-CLM-019 | Digital filter | De-emphasis control lines are wired to the SM5841s | SRC-20 block diagram | VERIFIED (presence); UNKNOWN (use) | M | Must confirm inactive in normal playback | EXP-010 |
| MPC3K-CLM-020 | Character | The MPC3000 path audibly colors undriven line-level program | Conflicting anecdote only (SRC-28) | UNKNOWN | — | Decides whether the MPC stage is more than linear + quantizer | EXP-009, -010, -014 |

### Chain

| ID | Subsystem | Claim | Evidence / source | Status | Conf. | Implementation impact | Hardware test |
|---|---|---|---|---|---|---|---|
| CHAIN-CLM-001 | Interstage | SP output level is undocumented in retrieved sources; MPC sensitivity is documented | Sections 10, 18 | VERIFIED (as a statement about the evidence) | H | Interstage default unset | EXP-005, -009 |
| CHAIN-CLM-002 | Interstage | A line-level SP output can overdrive the MPC input depending on record level | MPC3K-CLM-007 | PROVISIONAL | M | Interstage trim is physically meaningful | EXP-012 |
| CHAIN-CLM-003 | Bandwidth | SP hold images between 13 and 20 kHz lie inside the MPC passband and would be recorded | SP12-CLM-012, -020; MPC3K-CLM-001 | SIMULATED (follows from two models) | M–H | Internal analog-proxy rate must carry images | EXP-012 |
| CHAIN-CLM-004 | Stereo | SP stage has no historical stereo path; MPC stage does | SP12-CLM-015, -017; MPC3K-CLM-012 | STRONGLY SUPPORTED | H | Stereo SP is a product abstraction | EXP-007 |
| CHAIN-CLM-005 | Rates | SP rate / 44.1 kHz = 3125/5292; SP rate / 48 kHz = 625/1152 | Arithmetic on SP12-CLM-002 | SIMULATED on a PROVISIONAL constant | M | Resampler design | EXP-001 |
| CHAIN-CLM-006 | Bandwidth | Cascade baseband is set by the SP stage | SP12-CLM-001; MPC3K-CLM-001 | STRONGLY SUPPORTED | H | — | EXP-012 |
| CHAIN-CLM-007 | Latency | The full path cannot be zero latency; magnitude unknown | Architecture (analog filters, FIR converter filters, resamplers) | STRONGLY SUPPORTED | H | Latency reporting required | EXP-004, -010 |
| CHAIN-CLM-008 | History | Resampling SP-1200 output into an MPC3000 was a common production practice | None gathered | SPECULATIVE | L | No authenticity claim may rest on it | — |

---

## 35. Decision ledger

Decisions are choices, not facts.

| ID | Question | Options | Supporting claims | Current decision | Conf. | Reversibility | Reopens if |
|---|---|---|---|---|---|---|---|
| CHAIN-DEC-001 | Which product path (A, B, C)? | A / B / C | All | NOT CHOSEN. Reference model implements B as a superset with replaceable, bypassable blocks | — | Full | Measurements complete |
| CHAIN-DEC-002 | SP machine-rate constant | 26 040 / 26 041.67 / measured | SP12-CLM-001, -002 | 26 041.6667 Hz, provisional | M | Full (one constant) | Schematic or EXP-001 disagrees |
| CHAIN-DEC-003 | SP output path in the model | ch 7–8 / ch 5–6 / ch 3–4 / mix / ch 1–2 | SP12-CLM-012…016 | Output filter is a selected replaceable block; ch 1–2 excluded from MVP; canonical default UNDECIDED | M | Full | Response data available |
| CHAIN-DEC-004 | SP pitch | Unity only / tuned round trip | SP12-CLM-009, -010 | Unity only in MVP; tuned round trip deferred as labeled extreme mode | H | Full | Product direction |
| CHAIN-DEC-005 | SP stereo abstraction | Dual mono / linked dual mono / slot-skewed / mono sum / M-S | CHAIN-CLM-004 | Linked dual mono, shared sampling instants, identical coefficients; labeled PRODUCT ABSTRACTION | H | Full | EXP-007 shows material skew worth offering |
| CHAIN-DEC-006 | MPC modeling level | Identity / linear + quantizer + clamps / nonlinear | MPC3K-CLM-015, -020 | Linear responses + 16-bit quantizer + explicit clamps, all placeholders | M | Full | EXP-009/-010 show level-dependent residual |
| CHAIN-DEC-007 | Noise | On / off / omitted | Section 27 | OMITTED for both machines | H | Full | EXP-006 shows audible, characteristic noise |
| CHAIN-DEC-008 | Jitter | Model / reject | MPC3K-CLM-009; SP12-CLM-002 | REJECT | H | Full | Measured sidebands attributable to clock |
| CHAIN-DEC-009 | Power supply | Model / reject | MPC3K-CLM-008 | REJECT | H | Full | Measured supply-correlated modulation |
| CHAIN-DEC-010 | Tolerance / channel randomization | Core / optional / defer / reject | — | Product REJECT; research DEFER | H | Full | Second unit measured |
| CHAIN-DEC-011 | Converter strategy | A–F per converter | Section 29 | SP: A + C. MPC: C. INL/DNL/glitch: F | M | Full | Transfer measurements |
| CHAIN-DEC-012 | Meaning of a future drive control | Input level / calibration offset / interstage / output / macro | Section 26 | No drive control defined. Only physically mapped candidates are SP input level and MPC record level | H | Full | Product design phase |
| CHAIN-DEC-013 | Reverse order MPC→SP | Add / experiment only | — | Experiment only | H | Full | EXP-013 result and product decision |
| CHAIN-DEC-014 | Interstage trim | None / fixed / exposed | CHAIN-CLM-001, -002 | Explicit calibrated variable; default UNSET | H | Full | RD-P0-03 closed |
| CHAIN-DEC-015 | Dither in SP quantizer | Add / none | SP12-CLM-024 | None added | M | Full | EXP-002 low-level test shows dither-like behavior |
| CHAIN-DEC-016 | Sampler workflow mechanisms | Include / exclude | SP12-CLM-022 | Exclude (memory limits, truncation, loops, envelopes, velocity, sequencer) | H | Full | — |

---

## 36. Experiment registry

All experiments: **STATUS NOT EXECUTED. RESULT none. No outcome is claimed.** Artifact paths are planned locations.

| ID | Question | Hypothesis | Depends on | Input / configuration / procedure | Metrics | Decision criterion | Artifact path | Impact |
|---|---|---|---|---|---|---|---|---|
| CHAIN-EXP-001 | What is the SP sample rate? | 26 041.67 Hz | SP unit | Load a sample holding a sine of known period in samples; measure output frequency and the clock spur against the calibrated interface clock | Hz, ppm | Replace constant if outside measurement uncertainty | /reference/hardware/sp1200/unit_001/digital/ | DEC-002 |
| CHAIN-EXP-002 | SP input chain and quantizer transfer | AA response as SP-12; ideal 12-bit with clamp | Sample export route | Record sweeps, ramps, stepped and low-level sines at each gain; export sample data | Response, fold-back, code transitions, clamp codes | Fit filter; select rounding rule | …/sp1200/unit_001/digital/, /linear/ | RD-P0-01, -02; RD-P1-05 |
| CHAIN-EXP-003 | SP DAC, hold and unity playback | Full-period hold; identity at unity | Sample import route | Load synthetic 12-bit data; capture at each output | Hold fraction, droop, images, transfer linearity | Confirm or replace R6/R7 | …/sp1200/unit_001/digital/ | CLM-020, -026 |
| CHAIN-EXP-004 | SP output paths | Filters differ as documented | EXP-003 | Same sample at every output and contact, and MIX OUT | Complex response per path, to 96 kHz | Populate R8/R9; choose default | …/sp1200/unit_001/linear/ | RD-P0-01, -04 |
| CHAIN-EXP-005 | SP level calibration | — | Calibrated interface | Stepped sine at each gain; FS sine playback | Volts for FS in and out; clip onset | Close RD-P0-02 | …/sp1200/unit_001/calibration/ | RD-P0-02, -03 |
| CHAIN-EXP-006 | SP noise and spurs | Spurs at 26.04 and 208.33 kHz | — | Idle and loaded captures at 192 kHz | Spectrum, hum, DC | Keep noise OMITTED unless characteristic | …/sp1200/unit_001/noise/ | DEC-007 |
| CHAIN-EXP-007 | SP inter-channel skew | 4.8 µs per slot | EXP-003 | Same sample triggered on two channels | Inter-channel delay vs channel pair | Offer slot-skew research config or not | …/sp1200/unit_001/stereo/ | DEC-005 |
| CHAIN-EXP-008 | MPC digital transparency | S/PDIF → storage is bit-exact; reduction rule unknown | S/PDIF source | Sample known data digitally and via analog; save; compare | Bit differences; low-level harmonic signature | Select rule for R13 | /reference/hardware/mpc3000/unit_001/digital/ | RD-P0-05 |
| CHAIN-EXP-009 | MPC input chain + ADC | Linear to FS; clip location unknown | — | Stimuli at each switch position and several pot positions; save files | Response, FS volts, clip onset, overload recovery | Populate R11/R12 | …/mpc3000/unit_001/linear/, /nonlinear/ | RD-P0-06 |
| CHAIN-EXP-010 | MPC DAC + output | Linear; flat to 20 kHz | — | Load synthetic 16-bit sounds; capture main out | Response, group delay, THD, IMD, noise, FS volts | Populate R14/R15; test CLM-020 | …/mpc3000/unit_001/linear/, /nonlinear/, /noise/ | RD-P0-05, -06; RD-P1-07, -12 |
| CHAIN-EXP-011 | MPC main vs individual | Same within tolerance | EXP-010 | Same sound to both paths | Response and level differences | Decide whether paths differ in model | …/mpc3000/unit_001/linear/ | RD-P1-08 |
| CHAIN-EXP-012 | Physical cascade | Images pass; overload depends on record level | EXP-005, -009 | SP output into MPC input at documented settings | Captured files; level at each node | Set interstage default | /reference/hardware/cascade/ | RD-P0-03 |
| CHAIN-EXP-013 | Order | Small difference unless MPC input driven | Both units | SP→MPC vs MPC→SP on four material types (≤ 2.3 s excerpts) | Section 32 metric set | Informational | /reference/hardware/cascade/ | DEC-013 |
| CHAIN-EXP-014 | Level-matched cascade | — | EXP-012 | DRY / SP / MPC / SP→MPC / MPC→SP | Section 32 metric set | Informational | /reference/hardware/cascade/ | CLM-020 |
| CHAIN-EXP-015 | IMD suite | Products explained by sampling and quantization | EXP-002…-010 | SMPTE, CCIF, multitone on each machine | Product levels | Any unexplained product opens a nonlinear-block investigation | …/nonlinear/ | DEC-006, -011 |
| CHAIN-EXP-016 | Null-framework self-test | Framework nulls an ideal reference to numerical floor | None | Simulation only | Residual of identical signals after alignment | Framework accepted when its own floor is known | /research/sim/ | Validation |
| CHAIN-EXP-017 | Skeleton vs published SP-12 figures | Skeleton reproduces the alias/image pattern reported in SRC-04 qualitatively | None | Simulation only: sweep through R3–R8 with placeholder filters | Spectrogram pattern | Sanity check only; never evidence about hardware | /research/sim/ | Reference bring-up |
| CHAIN-EXP-018 | Listening test | — | Fitted models | Section 33 | Blind scores | — | /research/listening/ | Product decisions |
| CHAIN-EXP-019 | SP schematic extraction and SPICE | Responses consistent with SRC-04 | Readable copy of SRC-01 | Transcribe AA, channel-filter, mix and clock circuits; AC analysis | Transfer functions, corners, Q, gains, clock divider | Close RD-P0-01 documentarily | /reference/sources/sp1200/ | RD-P0-01, CLM-002 |
| CHAIN-EXP-020 | MPC schematic extraction and SPICE | Low-order filters | SRC-20 scan | Transcribe AD/DA and 8DACS analog sections; AC analysis | Transfer functions, gains, coupling poles, FS volts | Close RD-P0-06 documentarily | /reference/sources/mpc3000/ | RD-P0-06, RD-P1-12 |

---

## 37. Conflict ledger

| # | Claim | Source A | Source B | Why they may differ | Revision? | Output path? | Method? | Current verdict | Resolving test |
|---|---|---|---|---|---|---|---|---|---|
| C-01 | SP-12 family sample rate | 27.5 kHz "in the specifications" (as reported by SRC-04) | 26.04 kHz (SRC-05); 26 kHz tone measured (SRC-04) | Spec-sheet figure vs actual clock | No | No | Measurement vs literature | 26.04 kHz | EXP-001, -019 |
| C-02 | Output reconstruction filtering | "Reconstruction filter deliberately omitted" (SRC-06 relaying Rossum) | "Output filter is order 5" (SRC-04); "six of eight voices had a 4-pole low-pass" (tertiary wiki); "simple low-pass" on 3–6 (owners) | Different channels; fit order vs analog order; loose wording | No | **Yes** | Mixed | Channel dependent: none on 7–8, fixed low-pass on 3–6, SSM2044 on 1–2. Orders UNKNOWN | EXP-004, -019 |
| C-03 | How to reach the unfiltered signal on ch 1–6 | Owner's manual: plug type selects filtered vs unfiltered (SRC-03 excerpt, wording ambiguous in the extract) | Folklore: insert the plug halfway | Same TRS jack described two ways | Reissue has separate jacks | Yes | — | Contact mapping UNRESOLVED | EXP-004, -019 |
| C-04 | Per-voice VCA and ADSR | Tertiary wiki: analog VCA + ADSR per voice | SRC-09: level by multiplying DAC; SRC-04: digital decay envelope | Confusion with other E-mu designs | No | No | — | No classical VCA; level DAC PROVISIONAL | EXP-019 |
| C-05 | What makes the SP sound | "12-bit" resolution (popular) | SRC-04: output imaging and tuning algorithm dominate | Listening description vs mechanism | No | Yes | Measurement vs anecdote | Mechanism view adopted; "12-bit" rejected as a specification | EXP-002…-004 |
| C-06 | MPC3000 character | "Neutral, no sound of its own" (SRC-28) | "Very lo-fi, distinct" (SRC-28) | Uncontrolled comparisons, level differences, pitched playback, digital filters in use | Unknown | Unknown | Anecdote both sides | UNRESOLVED | EXP-009, -010, -014 |
| C-07 | SP AA corner | ~15 kHz attenuation onset on SP-12 (SRC-04) | "Upper limit around 14 kHz" (SRC-08 fragment, garbled) | Different definitions of corner; SP-12 vs SP-1200 | Possible | No | Measurement vs book | UNKNOWN for SP-1200 | EXP-002, -019 |
| C-08 | SP bit depth | "8-bit" (forum post) | 12-bit linear (SRC-05) | Error | No | No | — | 12-bit; source A discarded | — |

---

## 38. Failure register

| # | What failed or was disproved | Detail | Consequence |
|---|---|---|---|
| F-01 | Text extraction of the SP-1200 service manual | Public scan is image-only; OCR layer holds watermark lines only | No SP-1200 schematic values or theory-of-operation text in this pass → EXP-019 |
| F-02 | Retrieval of the SP-12 service manual | Blocked | Same |
| F-03 | Retrieval of the GroupDIY re-creation thread | Blocked; snippets only | SP12-CLM-006, -007 rest on excerpts; -007 held at PROVISIONAL |
| F-04 | Deriving MPC3000 filter transfer functions from OCR | Values readable, net connectivity not | No corner frequencies stated; nothing guessed → EXP-020 |
| F-05 | Locating the AK5328 datasheet | Searches returned other AKM parts | ADC filter response, latency and full-scale level UNKNOWN |
| F-06 | Assumption: the SP has a discrete ADC chip | Disproved by SRC-04/-09/-10 (SAR around the playback DAC) | Converter model simplified |
| F-07 | Assumption: MPC3000 uses 16-bit converters | Disproved by SRC-20 (18-bit ADC and DAC) | 16 bits is storage only |
| F-08 | Assumption: SP has a per-voice VCA stage in the signal path | Unsupported; removed from architecture | Block deleted |
| F-09 | Assumption: the signature SP character transfers to a unity-pitch mix path | Weakened by SRC-04 | Tuned round trip separated as an extreme mode |
| F-10 | Hope that interstage level could be set from specifications | SP output level undocumented | P0 debt |

Failed experiments, diverging models, bad fits, numerically unstable approaches: **none, because no experiment or model was run.**

---

## 39. Rejected ideas

| Idea | Verdict | Reason |
|---|---|---|
| Generic bitcrusher = SP-1200 | REJECTED | Omits AA filter, the specific 26.04 kHz grid, hold images and channel filters; SRC-04 shows quantization is the smallest of the documented effects |
| Generic saturation = MPC3000 | REJECTED | No evidence of any nonlinearity below clip |
| Random vintage noise | REJECTED | No measured noise profile |
| Vinyl noise | REJECTED | Not part of either machine |
| Fake clock jitter | REJECTED | Crystal-derived synchronous clocks; no measured effect |
| Arbitrary low-pass | REJECTED | Real filters exist and are obtainable; a guessed cutoff is not a model |
| Generic tanh warmth | REJECTED | No supporting transfer measurement |
| One waveshaper for an entire machine | REJECTED | The dominant mechanisms are linear filtering, sampling and hold, which a memoryless curve cannot represent |
| Random stereo mismatch | REJECTED | No evidence; damages image |
| Hysteresis | REJECTED | No magnetic component in either signal path per parts evidence |
| Transformers | REJECTED | None in the MPC3000 audio parts list (the only transformer-type parts are power and a pulse transformer on the mains filter board); none evidenced in the SP-1200 audio path |
| Repeated ADC/DAC stages not in the hardware | REJECTED | One conversion pair per machine |
| "12-bit warmth" as a specification | REJECTED | Listening description; the measurable content is 12-bit quantization error near −72…−74 dB |
| "MPC punch" as a specification | REJECTED until tied to a measured mechanism | No mechanism identified |
| SSM2044 dynamic filter on a mix bus | DEFERRED | Real, but envelope is note-triggered; undefined for continuous program |
| Tuned round trip as default | DEFERRED to labeled extreme mode | Historically real workflow; unsuitable for normal mix-bus use |
| Converter INL/DNL and glitch modeling | DEFERRED | Poorly identifiable; may cancel in the SP; no evidence in the MPC |
| Power-supply sag | REJECTED | Regulated rails, line-level loads |
| Automatic loudness compensation or hidden limiting | REJECTED | Violates full-mix safety policy |

---

## 40. Research debt

### P0 — blocks a defensible reference architecture (6 open)

| ID | Question | Why it matters | Best current hypothesis | Evidence needed | Test | Dependency | Implementation impact |
|---|---|---|---|---|---|---|---|
| RD-P0-01 | SP analog transfer functions: AA filter, ch 3–4 and 5–6 filters, mix path | Largest audible contributors after the sample rate itself | Multi-section active low-pass near 13–15 kHz in; lower-order low-pass out | Schematic values or measurement | EXP-019, -002, -004 | Readable SRC-01 or unit | R3, R8, R9 are placeholders until closed |
| RD-P0-02 | SP gain structure: input sensitivity per gain, ADC full-scale volts, output volts for full scale, clip points | Without it no level in the model has physical meaning | Line-level class; unknown | Measurement or schematic | EXP-005, -019 | Unit | R0, R2, R5, R9 calibration |
| RD-P0-03 | SP → MPC interstage calibration | Decides whether and how the MPC input is driven | User-set record level; no canonical value | RD-P0-02 + MPC full-scale volts | EXP-009, -012 | RD-P0-02, -06 | R10 default |
| RD-P0-04 | SP canonical output path and MIX OUT topology (what is summed, pre or post filter, contact mapping) | Defines which chain the product claims to represent | Mix sums post-filter channels | Schematic or measurement | EXP-004, -019 | Unit or SRC-01 | R8 selection; mono-sum mode |
| RD-P0-05 | MPC machine-domain behavior at unity: bit transparency, 18 → 16-bit rule, mixer scaling | Decides whether any MPC digital block exists besides a 16-bit quantizer | Transparent at unity; truncation or rounding | Bit-level tests | EXP-008, -010 | Unit, S/PDIF source | R13, R14 |
| RD-P0-06 | MPC analog responses and levels: input chain, clip location, I/V gain, output filter, full-scale volts | Decides whether the MPC analog stages contribute anything, and sets calibration | Low-order, flat in band, clip above converter full scale | Schematic extraction or measurement | EXP-020, -009, -010 | SRC-20 scan or unit | R11, R12, R15 |

### P1 — important before production modeling (12 open)

| ID | Question | Why | Hypothesis | Evidence / test | Dependency | Impact |
|---|---|---|---|---|---|---|
| RD-P1-01 | AD7541 datasheet figures, grade fitted, SAR timing and sample-and-hold aperture | Confirms converter assumptions | Standard grade; adequate settling | Datasheet; EXP-019, -002 | — | Converter strategy |
| RD-P1-02 | AK5328 datasheet: decimation response, group delay, full-scale input, overload behavior | Band edge, latency, clip | Linear-phase FIR; stopband near 24 kHz | Datasheet; EXP-009 | — | R12 |
| RD-P1-03 | SM5841 datasheet: response, group delay, rounding, de-emphasis logic | Band edge, latency | Linear-phase FIR | Datasheet; EXP-010 | — | R15 |
| RD-P1-04 | SP level-DAC: is maximum level unity; effect on resolution | Whether a gain or extra quantizer exists at unity | Unity at maximum | EXP-003 | — | R6 |
| RD-P1-05 | SP quantizer: encoding, rounding rule, offset, dither-like behavior | Low-level character | Floor-type SAR, analog-noise dither small | EXP-002 | Export route | R5 |
| RD-P1-06 | SP noise and spur spectrum | Noise policy | Spurs at 26.04 / 208.33 kHz | EXP-006 | — | DEC-007 |
| RD-P1-07 | MPC noise, THD, IMD vs level | Tests CLM-020 | At or below 16-bit limits | EXP-010, -015 | — | DEC-006 |
| RD-P1-08 | MPC main vs individual outputs | Path definition | Equivalent | EXP-011 | — | R15 variants |
| RD-P1-09 | Equivalence of SP-12 and SP-1200 analog and playback circuits | Licenses use of SRC-04 | Largely unchanged (SRC-06) | Schematic comparison | SRC-01, -02 | Confidence of CLM-008, -009 |
| RD-P1-10 | Audio-relevant differences across SP-1200 revisions (1987, 1993, 1997, Rossum 2020/2021) | One model must not merge revisions | Audio path unchanged except SSI2144 | Service notes, ECOs, measurements | — | Revision table |
| RD-P1-11 | SP multiplex slot skew and hold fraction | Stereo abstraction; droop | 4.8 µs per slot; near full-period hold | EXP-003, -007 | — | R7; DEC-005 |
| RD-P1-12 | MPC output level meaning ("6 dBm"), full-scale volts, coupling poles | Output calibration, LF phase | +6 dBm nominal | EXP-010, -020 | — | R15 |

### P2 — refinement / hardware fit

| ID | Question |
|---|---|
| RD-P2-01 | SP tuning table and accumulator precision (extreme mode only) |
| RD-P2-02 | Unit-to-unit tolerance |
| RD-P2-03 | SSM2044 channel behavior with continuous program |
| RD-P2-04 | AK5328 overload recovery dynamics |
| RD-P2-05 | MPC de-emphasis line behavior with emphasized S/PDIF sources |
| RD-P2-06 | Low-level linearity of both converter systems |

### P3 — historical / optional

| ID | Question |
|---|---|
| RD-P3-01 | Origin of the 27.5 kHz SP-12 specification figure |
| RD-P3-02 | MPC3000 operating-system versions and limited-edition hardware differences |
| RD-P3-03 | Documentary evidence for SP → MPC3000 resampling as period practice |
| RD-P3-04 | MPC3000 pitch-interpolation algorithm |

---

## 41. Minimum defensible MVP

The smallest reference model the evidence supports. Nothing is added to make it more dramatic.

**Included (supported):**
1. SP machine-rate domain at 26 041.67 Hz (provisional constant).
2. SP 12-bit quantizer with explicit code clamp.
3. SP zero-order hold.
4. SP output filter as a selected block with three states: none (ch 7–8, fully supported), ch 5–6, ch 3–4 (the latter two inactive until RD-P0-01 closes).
5. SP anti-alias filter block (inactive placeholder until RD-P0-01 closes; the model is not a valid SP model without it, and must say so).
6. MPC 44.1 kHz domain with 16-bit quantizer and explicit full-scale clamp.
7. Linked dual-mono stereo for the SP stage, labeled as a product abstraction.
8. Explicit calibration variables (input, interstage, output), unset until P0 closes.

**Excluded (unsupported today):** any nonlinear analog block, noise, jitter, supply effects, tolerance variation, SSM2044 channels, tuned playback, MPC mixer arithmetic, converter error models.

Honest statement of what this MVP is: a numerical skeleton of documented digital formats. Until the SP filters are populated it is a research harness, not a model of either machine.

**Priority sonic mechanisms.**

SP-1200:

| Rank | Mechanism | Evidence | Expected contribution | Complexity | Hardware fit | MVP | Refinement |
|---|---|---|---|---|---|---|---|
| 1 | 26.04 kHz band limit | VERIFIED | High | Low | Confirm | Yes | No |
| 2 | Hold images / channel filter choice | VERIFIED | High | Low | Yes | Yes | Yes |
| 3 | AA filter shape and fold-back | LITERATURE-DERIVED | Medium–high | Low | Yes | Placeholder | Yes |
| 4 | ADC clamp when driven | PROVISIONAL | High when driven | Low | Yes | Boundary | Yes |
| 5 | 12-bit quantization | VERIFIED | Low–medium | Low | Minor | Yes | Rule only |
| 6 | Hold droop | SIMULATED | Low | None | Minor | Yes | No |
| 7 | Analog stage behavior | UNKNOWN | UNKNOWN | — | Yes | No | Maybe |

MPC3000:

| Rank | Mechanism | Evidence | Expected contribution | Complexity | Hardware fit | MVP | Refinement |
|---|---|---|---|---|---|---|---|
| 1 | Input / ADC overload when driven | PROVISIONAL | High when driven; none otherwise | Low | Yes | Boundary | Yes |
| 2 | Converter digital filters (band edge) | VERIFIED architecture | Low | Low | Datasheet or measure | Placeholder | Yes |
| 3 | 16-bit reduction | VERIFIED storage | Very low | Low | Minor | Yes | Rule only |
| 4 | Analog filters and coupling poles | UNKNOWN values | Low | Low | Yes | Placeholder | Yes |
| 5 | Anything else | UNKNOWN | UNKNOWN | — | Yes | No | Only on evidence |

SP → MPC cascade:

| Rank | Mechanism | Evidence | Expected contribution | Complexity | Hardware fit | MVP | Refinement |
|---|---|---|---|---|---|---|---|
| 1 | SP stage as a whole | See above | Dominant | — | Yes | Yes | Yes |
| 2 | Interstage level into MPC input | PROVISIONAL | Decides whether the MPC stage does anything audible | Low | Yes | Variable, unset | Yes |
| 3 | SP images carried through the MPC passband | SIMULATED | Medium | Low | Yes | Yes | No |
| 4 | Cumulative group delay and latency | STRONGLY SUPPORTED | Low–medium | Low | Yes | Reported | Yes |
| 5 | Second quantizer | VERIFIED | Negligible | Low | No | Yes | No |

---

## 42. Production-readiness gate

**SP-1200 research gates**

| Item | Classification |
|---|---|
| Input topology | PARTIALLY KNOWN |
| AA filter | PARTIALLY KNOWN (class known; values REQUIRE schematic read or HARDWARE MEASUREMENT) |
| ADC | PARTIALLY KNOWN |
| Sample rate | KNOWN (nominal); exact constant PARTIALLY KNOWN |
| Bit depth | KNOWN |
| Storage representation | PARTIALLY KNOWN (12-bit linear known; encoding unknown) |
| Playback behavior | KNOWN |
| DAC | PARTIALLY KNOWN |
| Reconstruction | KNOWN qualitatively per channel; values REQUIRE HARDWARE MEASUREMENT |
| Main (mix) output | PARTIALLY KNOWN |
| Individual output | PARTIALLY KNOWN |
| Nominal level | UNKNOWN → REQUIRES HARDWARE MEASUREMENT |
| Clip behavior | UNKNOWN → REQUIRES HARDWARE MEASUREMENT |
| Bandwidth | PARTIALLY KNOWN |
| Noise | UNKNOWN → REQUIRES HARDWARE MEASUREMENT |

**MPC3000 research gates**

| Item | Classification |
|---|---|
| Input topology | PARTIALLY KNOWN |
| AA filter | PARTIALLY KNOWN (analog values unextracted; digital decimation response unknown) |
| ADC | KNOWN (part, architecture); performance PARTIALLY KNOWN |
| Sample rate | KNOWN |
| Bit depth | KNOWN (16 stored, 18 converted) |
| Storage representation | KNOWN (16-bit linear); reduction rule UNKNOWN |
| Playback behavior | PARTIALLY KNOWN (arithmetic unknown) |
| DAC | KNOWN |
| Reconstruction | PARTIALLY KNOWN |
| Main output | PARTIALLY KNOWN |
| Individual output | PARTIALLY KNOWN |
| Nominal level | PARTIALLY KNOWN |
| Clip behavior | UNKNOWN → REQUIRES HARDWARE MEASUREMENT |
| Bandwidth | KNOWN (stated 20 Hz – 20 kHz) |
| Noise | UNKNOWN → REQUIRES HARDWARE MEASUREMENT |

**Cascade gate**

| Item | Classification |
|---|---|
| SP → MPC level calibration | UNRESOLVED |
| Stereo path | PROVISIONAL (product abstraction on the SP side) |
| Rate-domain architecture | STRONGLY SUPPORTED |
| Converter strategy | PROVISIONAL |
| Noise strategy | PROVISIONAL (omit) |
| Clock strategy | STRONGLY SUPPORTED (deterministic grids, no jitter) |
| Output path | UNRESOLVED |

**Production start gate**

| Condition | State |
|---|---|
| P0 debt closed | NO (6 open) |
| Signal paths reconstructed | PARTIAL (block level yes; component level no) |
| Rate domains known | YES, with one provisional constant |
| Converter strategy chosen | PROVISIONAL |
| Filter topology known or explicitly provisional | Explicitly provisional (placeholders) |
| Gain staging defined | NO |
| Unknown blocks replaceable | YES by design (section 28) |
| Measurement plan ready | YES (section 30) |
| Validation metrics defined | Definitions YES; thresholds NO |
| Copyright / source provenance clear | PARTIAL: the SP-1200 manual scan carries an owner-use-only notice; treat it as a reference to consult, not a document to redistribute. Only short factual extraction is used here |

Production coding is **not approved**. Document length is not evidence.

**Verdict: HARDWARE REQUIRED.**
- The MPC3000 half has no documented coloration mechanism for undriven program. Whether it contributes anything audible can only be answered by measurement.
- The SP-1200 half has a sound structural model but no levels and no filter numbers. Schematic extraction can supply filter numbers; levels, clip behavior, noise and the canonical output choice need a unit.
- Interstage calibration, which defines what "SP → MPC" means, needs both.
- A plausible DSP idea exists. That is not sufficient for BUILD or BUILD WITH CONDITIONS on a product claiming to model these machines.
- Work that may proceed now without hardware: EXP-016, -017, -019, -020, datasheet retrieval, and the reference harness around the verified skeleton.

---

## 43. Implementation roadmap

Phases only. Nothing here is implemented, and no build prompts are written.

| Phase | Content | Entry condition | Exit condition |
|---|---|---|---|
| 1 | Research closure without hardware: schematic extraction and SPICE (EXP-019, -020), datasheets (RD-P1-01…-03), null-framework self-test (EXP-016) | This package | Filter and level values documentary or explicitly still unknown |
| 2 | Hardware measurement campaign per section 30 | Units available; framework self-tested | Artifact set complete with metadata and checksums |
| 3 | SP reference blocks (R2–R9), offline, traceable | Phase 1 values | Blocks validated against Phase 2 validation set |
| 4 | MPC reference blocks (R11–R15) | Phase 1 values | Same |
| 5 | Cascade and level calibration (R0, R10, R16) | RD-P0-02, -03 closed | Cascade validated (EXP-012, -014) |
| 6 | Hardware-fit refinement and block reduction to Path C | Phases 3–5 | Simplified model justified by measured residuals and listening tests |
| 7 | Product model optimization (real-time, latency, CPU) | Path chosen (DEC-001) | Product model nulls against reference model within a defined tolerance |
| 8 | Plugin wrapper and UI | Phase 7 | — |
| 9 | Release candidate | All gates in section 42 | — |

**Policies that later phases must honor.**

*Reference model vs product model.* Reference: traceability, replaceable blocks, explicit machine-rate domains, diagnostic taps, offline correctness, physical meaning; not optimized. Product: real-time safety, CPU, latency, simple controls, stable automation; validated against the reference, never directly against folklore.

*Parameter philosophy (no UI).* Only dimensions that map to a model variable: input calibration level; SP input level (source level relative to SP full scale, with the 0/+20/+40 dB gain as a machine state); SP output path selection; interstage level (MPC record level); MPC input gain position; output trim; chain mode (machine bypasses). "Amount" or mix controls for a machine path are not physically meaningful and are not recommended unless defined as an explicit dry/wet blend with latency compensation and documented as non-historical.

*Three-layer separation (mandatory).* PRODUCT PARAMETERS (user-facing) / MACHINE PARAMETERS (calibrated constants: rates, filter coefficients, full-scale voltages, clamp levels) / RESEARCH CONFIGURATION (hypothesis switches: rounding rule, hold fraction, slot skew, placeholder selection). Factory presets never change ResearchConfiguration.

*Preset policy.* No presets now. Later: presets store product parameters only; machine calibration fixed; no research strategy hidden in a preset; no automatic loudness normalization; no unsupported authenticity claims; headroom class documented per preset.

*Bypass semantics.* PLUGIN BYPASS (latency-compensated passthrough), SP BYPASS, MPC BYPASS as distinct states. A bypassed machine removes all of its blocks, including its rate conversion and quantizer; if latency alignment is retained it is documented. Sub-layer bypasses exist in the reference model for diagnosis and are exposed in a product only if a measured, audible layer justifies it.

*Latency policy.*

| Source | Estimate |
|---|---|
| Host resamplers (in and out) | Implementation dependent |
| SP AA and channel filters (analog group delay) | UNKNOWN; sub-millisecond class expected |
| SP sampling and hold | ≤ 1.5 SP samples (≤ 58 µs) |
| MPC ADC decimation filter | UNKNOWN (datasheet) |
| MPC DAC interpolation filter | UNKNOWN (datasheet) |
| Nonlinear oversampling | Only around clamps; implementation dependent |
| Lookahead | None required by any supported mechanism |

| Candidate architecture | Class |
|---|---|
| Path A, linear analog responses only, no machine-rate domain | ZERO LATENCY POSSIBLE (minimum-phase IIR), but this is an equalizer and not a model of either machine |
| Path A with oversampled clamps | LOW LATENCY |
| Path B full sample path | LATENCY REQUIRED |
| Path C hybrid | LOW LATENCY to LATENCY REQUIRED depending on which rate domains survive |

Zero latency is not promised for any architecture containing a machine-rate domain.

*Real-time requirements.* No allocation in process; no locks in the audio path; deterministic reset; denormal protection; bounded solvers (none currently needed); stable under host-rate and block-size changes; machine-domain behavior invariant to block size; deterministic offline bounce; no asynchronous sonic state; explicit latency reporting.

*Full-mix safety.* Explicit headroom; DC handling; clip indication at each modeled boundary; stable stereo image; inter-sample-peak awareness at both ADC boundaries; no hidden limiter, normalization or loudness compensation.

*Reproducibility.* Every experiment preserves script, input, configuration, output, checksum, software versions, commit and environment. No notebook-only findings.

*Hardware artifact directory.*

```
/reference/hardware/sp1200/unit_001/
/reference/hardware/mpc3000/unit_001/
    metadata/  calibration/  linear/  nonlinear/  noise/  digital/  stereo/  transient/
/reference/hardware/cascade/
/reference/sources/{sp1200,mpc3000}/      (schematic transcriptions, SPICE decks)
/research/sim/   /research/fit/   /research/validation/   /research/listening/
```

Metadata per unit and session: unit ID, serial, revision, modification status, warm-up, interface, calibration, cables, I/O used, levels, sample rate, firmware/OS, checksums.

*Artifact labels.* SOURCE EVIDENCE / SIMULATION / HARDWARE MEASUREMENT / FIT RESULT / VALIDATION RESULT / LISTENING STIMULUS / REFERENCE AUDIO. The label is in the filename, the sidecar and any plot title. A simulated plot or WAV must never be presentable as a hardware measurement.

---

## 44. Machine-readable handoff

`SP1200_MPC3000_HANDOFF_V1.json` accompanies this document. It contains: project, research version, status flags (hardware measured false, listening tests false, production ready false, reference implementation "WITH_CONDITIONS"), sources, claims, decisions, experiments, research debt with open P0/P1 lists, signal paths, component inventory, rate plan, candidate architecture, measurement plan, validation plan, rejected approaches. It summarizes this Markdown package and does not replace it. Where the two differ, this document governs.

---

## 45. Sources

| ID | Reference |
|---|---|
| SRC-01 | https://archive.org/details/emu-sp-1200-service-manual-1987_202010 |
| SRC-02 | https://web.archive.org/web/20240702212643/https://www.theemus.com/documentation/sp12/SP12_Service_Manual.pdf |
| SRC-03 | https://www.samplekings.com/pdfs/SP1200%20User%20Manual.pdf |
| SRC-04 | https://ccrma.stanford.edu/~dtyeh/papers/yeh07_icmc_sp12.pdf |
| SRC-05 | https://www.rossum-electro.com/products/sp-1200 |
| SRC-06 | https://en.wikipedia.org/wiki/E-mu_SP-1200 ; https://en.wikipedia.org/wiki/E-mu_SP-12 |
| SRC-07 | https://www.youtube.com/watch?v=-ck6D1KUYEk |
| SRC-08 | Hyland, S. (2011). SP-1200: The Art and Science. 27Sens. ISBN 2953541012 |
| SRC-09 | https://groupdiy.com/threads/vintage-sampler-e-mu-sp1200-re-creation-and-improvement.57711/ |
| SRC-10 | https://gearspace.com/board/electronic-music-instruments-and-electronic-music-production/1294283-mksrec-1-12-bit-sampling-drum-machine-my-sp-1200-clone-2.html |
| SRC-11 | https://www.modwiggler.com/forum/viewtopic.php?t=212381 |
| SRC-12 | https://groupdiy.com/threads/sp1200-anti-aliasing-filter-made-variable-resonance.92782/ |
| SRC-13 | https://www.mpc-forums.com/viewtopic.php?p=227693 ; https://gearspace.com/threads/e-mu-sp12-sample-problem.904115/ |
| SRC-14 | https://headlinerhub.com/a-hip-hop-legend-everything-you-need-to-know-about-the-new-rossum-sp-1200.html ; https://musictech.com/news/e-mu-sp-1200-reissue-dave-rossum-electro-music-sp1200/ |
| SRC-20 | https://archive.org/details/akai_MPC3000_SERVICE_MANUAL |
| SRC-21 | http://studiorepair.com/gallery/Akai/MPC3000/slides/Akai_MPC3000_ADC_PCB__STUDIOREPAIR_10061002_1701196912.html |
| SRC-22 | https://www.audiophonics.fr/images2/5749/mXuryvt.pdf (Burr-Brown PDS-1168A) |
| SRC-23 | https://edn.com/18-bit-d-a-has-good-low-level-performance/ |
| SRC-24 | https://www.rogerlinndesign.com/support/support-mpc-3-10-faqs |
| SRC-25 | https://www.soundonsound.com/reviews/akai-mpc3000 |
| SRC-26 | https://www.manualslib.com/manual/207365/Akai-Mpc-3000.html |
| SRC-27 | https://www.mpc-forums.com/viewtopic.php?f=4&t=185061 |
| SRC-28 | https://gearspace.com/board/electronic-music-instruments-and-electronic-music-production/996069-akai-mpc-3000-what-makes-so-special-3.html |
| SRC-30…33 | Datasheets not retrieved in this pass (AD7541, SSM2044/SSI2144, AK5328, SM5841). SSI2144: https://www.soundsemiconductor.com/downloads/ssi2144datasheet.pdf (cited by SRC-06, not read) |

End of research package V1.
