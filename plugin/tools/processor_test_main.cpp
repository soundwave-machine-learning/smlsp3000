// Direct processor regression: retain oversized callbacks independently of the VST3 host contract.
#include "PluginProcessor.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <type_traits>
#include <vector>

static int checks = 0, failures = 0;
static void check(bool ok, const char* name, int rate, int precision) {
    ++checks;
    std::printf("%s %s rate=%d float%d\n", ok ? "PASS" : "FAIL", name, rate, precision);
    if (!ok) ++failures;
}

template <typename Sample>
static std::vector<Sample> render(int rate, int expectedLatency, const std::vector<Sample>& input,
                                  const std::vector<int>& blocks, bool requireOversized) {
    constexpr int preparedMaximum = 512;
    constexpr int precision = std::is_same_v<Sample, double> ? 64 : 32;
    SMLProcessor processor;
    processor.setPlayConfigDetails(2, 2, rate, preparedMaximum);
    processor.setProcessingPrecision(std::is_same_v<Sample, double> ? juce::AudioProcessor::doublePrecision
                                                                    : juce::AudioProcessor::singlePrecision);
    processor.prepareToPlay(rate, preparedMaximum);
    check(processor.rateSupported() && processor.getLatencySamples() == expectedLatency,
          "prepare_and_latency", rate, precision);
    const int frames = static_cast<int>(input.size() / 2);
    std::vector<Sample> output(input.size());
    juce::AudioBuffer<Sample> buffer(2, *std::max_element(blocks.begin(), blocks.end()));
    juce::MidiBuffer midi;
    int done = 0, largest = 0;
    std::size_t index = 0;
    while (done < frames) {
        const int n = std::min(blocks[index++ % blocks.size()], frames - done);
        largest = std::max(largest, n);
        for (int c = 0; c < 2; ++c)
            for (int m = 0; m < n; ++m)
                buffer.setSample(c, m, input[static_cast<std::size_t>((done + m) * 2 + c)]);
        juce::AudioBuffer<Sample> view(buffer.getArrayOfWritePointers(), 2, n);
        processor.processBlock(view, midi);
        for (int c = 0; c < 2; ++c)
            for (int m = 0; m < n; ++m)
                output[static_cast<std::size_t>((done + m) * 2 + c)] = view.getSample(c, m);
        done += n;
    }
    if (requireOversized)
        check(largest == 9000 && largest > preparedMaximum, "9000_samples_after_prepare_512", rate, precision);
    check(std::all_of(output.begin(), output.end(), [](Sample value) { return std::isfinite(value); }),
          "finite_output", rate, precision);
    processor.releaseResources();
    return output;
}

template <typename Sample>
static void run(int rate, int latency) {
    constexpr int precision = std::is_same_v<Sample, double> ? 64 : 32;
    const int inputFrames = 32768;
    std::vector<Sample> input(static_cast<std::size_t>((inputFrames + latency) * 2), Sample{});
    for (int m = 0; m < inputFrames; ++m) {
        const double t = static_cast<double>(m) / rate;
        input[static_cast<std::size_t>(m * 2)] = static_cast<Sample>(0.25 * std::sin(6.283185307179586 * 997.0 * t));
        input[static_cast<std::size_t>(m * 2 + 1)] = static_cast<Sample>(0.17 * std::sin(6.283185307179586 * 5321.0 * t));
    }
    const auto regular = render<Sample>(rate, latency, input, {512}, false);
    const auto irregular = render<Sample>(rate, latency, input,
        {1, 7, 500, 2048, 64, 3, 1000, 4096, 2, 1, 513, 8192, 9000}, true);
    check(regular.size() == irregular.size() &&
          std::memcmp(regular.data(), irregular.data(), regular.size() * sizeof(Sample)) == 0,
          "oversized_partition_bit_identical", rate, precision);
}

int main() {
    juce::ScopedJuceInitialiser_GUI init;
    const int rates[] = {44100, 48000, 88200, 96000, 176400, 192000};
    const int latencies[] = {298, 310, 426, 449, 682, 728};
    for (int i = 0; i < 6; ++i) {
        run<float>(rates[i], latencies[i]);
        run<double>(rates[i], latencies[i]);
    }
    std::printf("PROCESSOR OVERSIZED TEST: %d checks, %d failures\n", checks, failures);
    return failures == 0 ? 0 : 1;
}
