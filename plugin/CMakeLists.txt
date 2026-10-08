cmake_minimum_required(VERSION 3.22)
project(smlsp3000_plugin VERSION 0.7.0 LANGUAGES C CXX)
# SML SP-3000 plugin wrapper (Sprint 7, OWN-DEC-024..026): JUCE (pinned, see JUCE_PIN.json) around the unchanged native core.
# The core keeps its own floating-point policy (-ffp-contract=off, no fast-math) through its PUBLIC compile options.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()
if(NOT MSVC)
  set(CMAKE_CXX_FLAGS_RELEASE "-O2 -DNDEBUG" CACHE STRING "" FORCE)
endif()

# ---- pinned dependency check (plugin/JUCE_PIN.json) -------------------------------------------------------------
set(SMLSP3000_JUCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../third_party/JUCE" CACHE PATH "Approved local JUCE checkout")
set(SMLSP3000_JUCE_PINNED_COMMIT "f72bad64d29715216226685810c5196bd0d79d77")
set(SMLSP3000_JUCE_PINNED_TAG "8.0.9")
if(NOT EXISTS "${SMLSP3000_JUCE_DIR}/CMakeLists.txt")
  message(FATAL_ERROR "JUCE checkout not found at ${SMLSP3000_JUCE_DIR}. Retrieve the pinned release: git clone --depth 1 --branch ${SMLSP3000_JUCE_PINNED_TAG} https://github.com/juce-framework/JUCE third_party/JUCE")
endif()
find_package(Git QUIET)
if(GIT_EXECUTABLE)
  execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${SMLSP3000_JUCE_DIR}" rev-parse HEAD OUTPUT_VARIABLE juce_head OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
  if(NOT juce_head STREQUAL SMLSP3000_JUCE_PINNED_COMMIT)
    message(FATAL_ERROR "JUCE checkout commit '${juce_head}' does not match the pinned commit ${SMLSP3000_JUCE_PINNED_COMMIT} (tag ${SMLSP3000_JUCE_PINNED_TAG}); see plugin/JUCE_PIN.json")
  endif()
endif()

# ---- native core (framework independent) ------------------------------------------------------------------------
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../native" "${CMAKE_BINARY_DIR}/native")

# ---- JUCE --------------------------------------------------------------------------------------------------------
set(JUCE_MODULES_ONLY OFF)
add_subdirectory("${SMLSP3000_JUCE_DIR}" "${CMAKE_BINARY_DIR}/JUCE" EXCLUDE_FROM_ALL)

# Product identity: plugin/product_identity.json (centralised; do not change after fixtures exist)
juce_add_plugin(SMLSP3000
    PRODUCT_NAME "SML SP-3000"
    COMPANY_NAME "Soundwave Machine Learning"
    BUNDLE_ID "com.soundwavemachinelearning.smlsp3000"
    PLUGIN_MANUFACTURER_CODE SWML
    PLUGIN_CODE Sp3K
    FORMATS VST3 Standalone
    VST3_CATEGORIES Fx
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS TRUE
    COPY_PLUGIN_AFTER_BUILD FALSE
    VST3_AUTO_MANIFEST FALSE
    VERSION 0.7.0)

target_sources(SMLSP3000 PRIVATE src/PluginProcessor.cpp src/PluginEditor.cpp)
target_include_directories(SMLSP3000 PRIVATE src)
target_compile_definitions(SMLSP3000 PUBLIC
    JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_VST3_CAN_REPLACE_VST2=0
    JUCE_DISPLAY_SPLASH_SCREEN=0 JUCE_REPORT_APP_USAGE=0          # permitted under the AGPLv3 route (plugin/JUCE_PIN.json)
    JUCE_USE_XRANDR=0 JUCE_USE_XINERAMA=0 JUCE_USE_XCURSOR=0        # Linux dev container: these headers are not installed; cosmetic only
    JUCE_ALSA=$<IF:$<BOOL:${SMLSP3000_LINUX_ALSA}>,1,0> JUCE_JACK=0  # Linux dev container has no ALSA headers; Windows uses WASAPI/DirectSound
    JUCE_MODAL_LOOPS_PERMITTED=0)
option(SMLSP3000_LINUX_ALSA "Build the Linux standalone with ALSA (needs libasound2-dev)" OFF)
target_link_libraries(SMLSP3000 PRIVATE smlsp3000_core juce::juce_audio_utils juce::juce_audio_processors juce::juce_gui_basics
    PUBLIC juce::juce_recommended_config_flags juce::juce_recommended_warning_flags)
# No link-time optimisation (juce_recommended_lto_flags deliberately not used): the core's objects keep exactly the Sprint 6
# floating-point policy (-ffp-contract=off -fno-fast-math, PUBLIC on the core target) and are never re-optimised at link time.
# JUCE's recommended config flags add no fast-math. Recorded in evidence/sprint_07/build_record.json.

# ---- editor snapshot tool (development only; renders the editor to PNG under a virtual display) --------------------
juce_add_gui_app(smlsp3000_editor_snapshot PRODUCT_NAME "smlsp3000_editor_snapshot")
target_sources(smlsp3000_editor_snapshot PRIVATE tools/snapshot_main.cpp src/PluginProcessor.cpp src/PluginEditor.cpp)
target_include_directories(smlsp3000_editor_snapshot PRIVATE src)
target_compile_definitions(smlsp3000_editor_snapshot PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_DISPLAY_SPLASH_SCREEN=0 JUCE_REPORT_APP_USAGE=0 JUCE_USE_XRANDR=0 JUCE_USE_XINERAMA=0 JUCE_USE_XCURSOR=0 JUCE_ALSA=0 JUCE_JACK=0 JUCE_MODAL_LOOPS_PERMITTED=1 SMLSP3000_SNAPSHOT_TOOL=1 JUCE_STANDALONE_APPLICATION=1)
target_link_libraries(smlsp3000_editor_snapshot PRIVATE smlsp3000_core juce::juce_audio_utils juce::juce_audio_processors juce::juce_gui_basics juce::juce_recommended_config_flags juce::juce_recommended_warning_flags)

# ---- native VST3 host harness (development/validation only) ----------------------------------------------------
juce_add_console_app(smlsp3000_host_harness PRODUCT_NAME "smlsp3000_host_harness")
target_sources(smlsp3000_host_harness PRIVATE tools/host_harness_main.cpp)
target_compile_definitions(smlsp3000_host_harness PRIVATE JUCE_PLUGINHOST_VST3=1 JUCE_PLUGINHOST_VST=0 JUCE_PLUGINHOST_AU=0 JUCE_PLUGINHOST_LV2=0 JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_USE_XRANDR=0 JUCE_USE_XINERAMA=0 JUCE_USE_XCURSOR=0 JUCE_ALSA=0 JUCE_JACK=0 JUCE_MODAL_LOOPS_PERMITTED=1)
target_link_libraries(smlsp3000_host_harness PRIVATE juce::juce_audio_processors juce::juce_gui_basics juce::juce_recommended_config_flags juce::juce_recommended_warning_flags)

# ---- Preset Lab (development/authoring tool; separate targets, no change to the product targets above) ----------------
add_subdirectory(tools/preset_lab)
