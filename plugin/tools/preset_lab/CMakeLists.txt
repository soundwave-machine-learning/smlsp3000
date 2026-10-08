# SML SP-3000 Preset Lab - development/authoring targets (NOT the product). Same product sources (PluginProcessor/Editor) and the
# unchanged native core; the lab adds no DSP. Built as part of the plugin project: add_subdirectory(tools/preset_lab) in plugin/CMakeLists.txt.
set(SMLSP3000_LAB_COMMON_DEFS JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_DISPLAY_SPLASH_SCREEN=0 JUCE_REPORT_APP_USAGE=0 JUCE_USE_XRANDR=0 JUCE_USE_XINERAMA=0 JUCE_USE_XCURSOR=0
    JUCE_ALSA=$<IF:$<BOOL:${SMLSP3000_LINUX_ALSA}>,1,0> JUCE_JACK=0 JUCE_MODAL_LOOPS_PERMITTED=1 JUCE_STANDALONE_APPLICATION=1
    SMLSP3000_REPO_ROOT="${CMAKE_CURRENT_SOURCE_DIR}/../../.." SMLSP3000_LAB_BUILD_ID="${SMLSP3000_LAB_BUILD_ID}")
set(SMLSP3000_LAB_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../src")
set(SMLSP3000_LAB_SHARED "${CMAKE_CURRENT_SOURCE_DIR}/PresetCandidate.cpp" "${CMAKE_CURRENT_SOURCE_DIR}/LabEngine.cpp" "${SMLSP3000_LAB_SRC_DIR}/PluginProcessor.cpp" "${SMLSP3000_LAB_SRC_DIR}/PluginEditor.cpp")
find_package(Git QUIET)
if(GIT_EXECUTABLE AND NOT SMLSP3000_LAB_BUILD_ID)
  execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${CMAKE_CURRENT_SOURCE_DIR}" rev-parse HEAD OUTPUT_VARIABLE SMLSP3000_LAB_BUILD_ID OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
  set(SMLSP3000_LAB_COMMON_DEFS ${SMLSP3000_LAB_COMMON_DEFS} SMLSP3000_LAB_BUILD_ID="${SMLSP3000_LAB_BUILD_ID}")
endif()

# GUI tool (also runs the headless --validate/--roundtrip/--render/--snapshot modes)
juce_add_gui_app(smlsp3000_preset_lab PRODUCT_NAME "smlsp3000_preset_lab" COMPANY_NAME "Soundwave Machine Learning")
target_sources(smlsp3000_preset_lab PRIVATE LabApp.cpp ${SMLSP3000_LAB_SHARED})
target_include_directories(smlsp3000_preset_lab PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}" "${SMLSP3000_LAB_SRC_DIR}")
target_compile_definitions(smlsp3000_preset_lab PRIVATE ${SMLSP3000_LAB_COMMON_DEFS})
target_link_libraries(smlsp3000_preset_lab PRIVATE smlsp3000_core juce::juce_audio_utils juce::juce_audio_devices juce::juce_audio_formats juce::juce_cryptography juce::juce_audio_processors juce::juce_gui_basics juce::juce_recommended_config_flags juce::juce_recommended_warning_flags)

# self-test (ctest preset_lab_test)
juce_add_console_app(smlsp3000_preset_lab_test PRODUCT_NAME "smlsp3000_preset_lab_test")
target_sources(smlsp3000_preset_lab_test PRIVATE lab_test_main.cpp ${SMLSP3000_LAB_SHARED})
target_include_directories(smlsp3000_preset_lab_test PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}" "${SMLSP3000_LAB_SRC_DIR}")
target_compile_definitions(smlsp3000_preset_lab_test PRIVATE ${SMLSP3000_LAB_COMMON_DEFS})
target_link_libraries(smlsp3000_preset_lab_test PRIVATE smlsp3000_core juce::juce_audio_utils juce::juce_audio_formats juce::juce_cryptography juce::juce_audio_processors juce::juce_gui_basics juce::juce_recommended_config_flags juce::juce_recommended_warning_flags)
find_program(SMLSP3000_XVFB_RUN xvfb-run)
enable_testing()
if(SMLSP3000_XVFB_RUN AND NOT WIN32)
  add_test(NAME preset_lab_test COMMAND "${SMLSP3000_XVFB_RUN}" -a -s "-screen 0 1280x800x24" $<TARGET_FILE:smlsp3000_preset_lab_test>)
else()
  add_test(NAME preset_lab_test COMMAND smlsp3000_preset_lab_test)
endif()
