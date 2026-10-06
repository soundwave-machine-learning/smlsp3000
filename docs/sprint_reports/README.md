# Sprint reports

Revision: execution V1 · 2026-10-06

One report per executed sprint, `SPRINT_NN_REPORT.md`, written only after the actual work (docs/AUTONOMOUS_BUILD_PROMPT.md, owner execution instruction §7E). A report never precedes execution and never carries its own ending commit hash; the ending hash is recorded in docs/PROJECT_HANDOFF.md and in the next report's starting state after the commit exists.

## Required sections

1. Sprint, title, contract revision and authorization reference
2. Starting commit, branch, working-tree state at start
3. Objective and scope mapping (contract subsystem permissions → actual repository paths)
4. Implementation completed (what exists now; what deliberately does not)
5. Commands executed (exact shell, working directory, tool versions, exit codes)
6. Tests executed and results (every listed VAL check; PASS / FAIL / BLOCKED / NOT EXECUTED)
7. Measurements and metrics (with artifact class labels)
8. Generated artifacts (paths, SHA-256, class, dataset role)
9. Assumptions
10. Deviations from the contract and their justification
11. Unresolved issues and blockers (gate ID, evidence, impact, options, next action)
12. Documentation updates
13. Confidence / status changes (only evidence-backed)
14. Human gates and hardware gates (OPEN items stated explicitly)
15. Final verdict: `PASS`, `BLOCKED`, or `PASS WITH EXTERNAL VALIDATION PENDING`
16. Continuation gate for the next sprint
17. Ending commit (filled in after the milestone commit by the handoff/next report, never guessed)

## Verdict vocabulary

- `PASS` — every mandatory automated gate of the contract executed and passed with evidence; no mandatory human/hardware gate inside the sprint's own definition of done is open.
- `BLOCKED` — a mandatory gate cannot be satisfied in this execution context; partial artifacts recorded truthfully; milestone not accepted.
- `PASS WITH EXTERNAL VALIDATION PENDING` — implementation and automated gates pass, and only a specifically named external human/hardware/platform gate remains that the contract itself places outside the sprint.

Artifact labels follow research §43: SOURCE EVIDENCE / SIMULATION / HARDWARE MEASUREMENT / FIT RESULT / VALIDATION RESULT / LISTENING STIMULUS / REFERENCE AUDIO.
