# SP-1200 → MPC3000 Full-Mix Processor — planning package

Revision: execution V2 (owner decision OWN-DEC-001) · 2026-10-06 · supersedes execution V1

Status: EXECUTION IN PROGRESS on branch `claude/autonomous-build` (owner implementation authorization 2026-10-06). Release NOT authorized. Hardware NOT measured.

**Sprint 1 executed (PASS); Sprint 2 hardware campaign BLOCKED / EXTERNAL HARDWARE REQUIRED; owner decision OWN-DEC-001 (2026-10-06) splits the work into Track A (software/reference implementation, provisional, may proceed) and Track B (hardware fit, deferred).** No DSP written yet; no machine model exists. Shipping path and SP default remain unselected. Reference B superset recommended. Plan: [execution plan V2](docs/EXECUTION_PLAN_V2.md) (submitted for owner approval).

**Claim boundary.** Until the hardware gate G-04 is actually completed, SML SP-3000 is described only as *a software instrument/effect inspired by and informed by documented SP-1200 / MPC3000 architecture and behaviour*. It is not an exact emulation, not hardware matched, not component accurate, not a measured SP-1200 or MPC3000, and not hardware validated. Current state: [project handoff](docs/PROJECT_HANDOFF.md); commands: [BUILD_COMMANDS](docs/BUILD_COMMANDS.md); reports: [sprint reports](docs/sprint_reports/).

Start with [delivery summary](docs/DELIVERY_SUMMARY.md), [research audit](docs/RESEARCH_AUDIT.md), [document index](docs/README.md), [eight-sprint index](docs/SPRINT_PLAN.md) and [acceptance matrix](docs/ACCEPTANCE_MATRIX.md). Exact source copies are underdocs/research; manifests provide integrity hashes. No implementation/sprint reports are fabricated.

The engineering package translates supplied research into requirement/interface/rate/gain/parameter/measurement/validation/state contracts. It preserves all6P0/12P1 blockers and keeps all20 experiments unexecuted. Eight contracts plus [autonomous prompt](docs/AUTONOMOUS_BUILD_PROMPT.md) can later be read directly from an authorized repository; no need for eight pasted prompts.

Next action: owner approves docs/EXECUTION_PLAN_V2.md §4 and supplies its §9 inputs so Sprint 3 (Track A) can start; separately, the stock-unit hardware campaign (G-04) and optional source access for CHAIN-EXP-019/020 remain open for Track B. Later hardware/listening/native gates are real prerequisites. No broad research restart, source repository mutation or production DSP occurred here. Unknown targets and licenses remain unknown; native AU/VST3/Windows/macOS delivery is not promised without the target matrix.
