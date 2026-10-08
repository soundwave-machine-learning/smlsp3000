# Paste into the next UI/preset task

Continue SML SP-3000 on this Windows PC. I want a UI and preset development pass for the working plugin, not Sprint 8 or release/publication work.

Repository: D:\SML Projects\SML-SP-3000
Branch: claude/autonomous-build
HEAD baseline: 38ff483ed6f75d080bfc5e06e32465e4804294ca
Build: D:\SML Builds\SML-SP-3000\windows-sprint7-release
JUCE: third_party\JUCE, 8.0.9, f72bad64d29715216226685810c5196bd0d79d77

Read AGENTS.md and docs/WINDOWS_TROUBLESHOOTING_REPORT.md, docs/UI_PRESET_HANDOFF.md, docs/PROJECT_HANDOFF.md and docs/BUILD_COMMANDS.md first. Then inspect the actual implementation and governing architecture/parameter/state documents.

The installed VST3 works in FL Studio according to my owner report. Executable SHA-256: E0D0B731698ED7739346D5C00FC9C15532925B04257DF7D9B070385ACB5F04E6. Keep it as rollback baseline; do not replace it without a separate installation decision.

The working tree is intentionally dirty. Preserve the approved max-block harness correction, new plugin/tools/processor_test_main.cpp, its CMake target and all documentation. Do not reset, clean, stash or assume HEAD includes these additions. No troubleshooting changes were committed.

Scope: original UI/assets and a compatible preset layer using the existing six product controls. Preserve DSP/JUCE, host IDs/order/ranges/defaults/mappings, VST3 identity, stereo buses, schema-v1 recall, smoothing/bypass, latency and block-boundary automation. No hidden DSP or research controls. No APVTS/state architecture rewrite merely for UI styling. Only INIT exists; no preset bank has been implemented.

Inspect the editor and baseline screenshots, then propose a concise UI direction and preset scope. Ask for missing visual references or audition material; do not pretend a theme or preset sound has been approved. Progress through authorized work without repeated permission requests. Material DSP, state-compatibility or parameter-semantic changes require a specific decision.

Validate UI/preset changes with existing Windows tests, reference comparisons and pluginval. Full native VAL-019/020/021/022 and plugin VAL-023/025/026 passed. Unit baseline remains 57/59: CHAIN-EXP-016 exact reproduction and CRLF integrity are unresolved. Callback p99.9 target and Windows sanitizer proof remain open. Do not weaken tests, regenerate goldens or invent PASS results.

The FL scan freeze came from D:\Audio recursively including archived Windows servicing DLLs. That path was backed up and disabled. Keep the broad root disabled; use actual plugin directories. Do not reset plugin databases.

Deliver implemented source/assets, actual before/after screenshots, exact preset values and audition status, validation results compared with baseline, staged hashes and updated handoff. Listening/UI acceptance remain mine. Do not start Sprint 8, merge main, publish or distribute.
