# Project brief and authorized scope

Revision: planning V1 · 2026-10-06

Status: DRAFT PLANNING CONTRACT. Documentation creation authorized; implementation and release not authorized.

## Goal and first useful result

Create a full-mix audio processor whose actual mechanisms are supported by a stock-vintage SP-1200 and stock MPC3000, with SP→MPC as the intended order. The first useful engineering result is a reproducible evidence/measurement harness and calibrated reference, not a release binary. B is recommended as the reference superset; shipping path unselected.

## Authorized work in this session

Audit supplied research, identify selected/unselected choices, P0/P1 debt, gates and contradictions, then generate complete engineering documents, **exactly eight** substantive sprint contracts and autonomous build orchestrator. Planning only; no production DSP. That authorization is satisfied by actual deliverable files. No source repository creation, commits, agent launch, dependency install, hardware operation, release or deployment is requested now.

## Product boundaries

Stereo mix-bus processing with a labeled linked dual-mono SP abstraction and real stereo MPC topology. Unity pitch, explicit gain/clip domains, fixed calibrated machine assets, no added vintage noise/sag/jitter/mismatch. Ch1–2 SSM2044 and tuned round-trip are deferred. Reverse order is experiment only. Sample memory, sequencer, voice allocation, loops, envelopes, disk emulator and velocity are not product tasks. Analog numerical response is not inferred from branding or forum descriptors.

## Targets and inputs

Supplied and inspected: Research package V1 dated2026-10-05; JSON handoff V1 same date. Neither supplies a repository, approved OS/CPU/plugin format/DAW matrix, toolchain, license budget, unit captures or hardware access. These are UNKNOWN rather than inherited from SPZERO or another project. Stock unit revision/modification/OS is established by G-04. Intended runtime target must be recorded before executable wrapper work. No specific old Mac, Windows version, JUCE choice or SDK assumption is imported from chat memory.

## Milestones and owner responsibility

S1 freezes execution context/commands and self-tests analysis; S2 validates hardware evidence, closes debt and freezes acceptance; S3/S4 fit SP/MPC references; S5 validates cascade and chooses product through listening; S6 builds optimized shared engine/parameters; S7 integrates approved plugin/hosts/UI; S8 produces reviewed reproducible candidate. Owner decisions/hardware/listening are real prerequisites. Autonomous routine implementation can continue after gates, but cannot invent evidence, waive human decisions or manufacture target passes.
