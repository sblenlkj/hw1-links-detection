from pathlib import Path
from time import perf_counter

from links_detector.finalizer import LinksFinalizer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = PROJECT_ROOT / "dataset" / "markdown" / "00_readme_example.md"
BENCHMARK_SIZE = 500
TOTAL_HIDDEN_BENCHMARK_SIZE = 4 * BENCHMARK_SIZE


def test_readme_example_benchmark() -> None:
    text = SAMPLE_PATH.read_text(encoding="utf-8")
    finalizer = LinksFinalizer()

    # Warm up once so one-time initialization does not distort the measurement.
    finalizer.extract(text)

    started = perf_counter()
    for _ in range(BENCHMARK_SIZE):
        finalizer.extract(text)
    elapsed = perf_counter() - started

    average_ms = elapsed / BENCHMARK_SIZE * 1000
    documents_per_second = BENCHMARK_SIZE / elapsed
    projected_2000_seconds = elapsed * (
        TOTAL_HIDDEN_BENCHMARK_SIZE / BENCHMARK_SIZE
    )

    print()
    print("LinksFinalizer local benchmark")
    print(f"sample:             {SAMPLE_PATH.name}")
    print(f"documents:          {BENCHMARK_SIZE}")
    print(f"total time:         {elapsed:.3f} s")
    print(f"avg/document:       {average_ms:.3f} ms")
    print(f"documents/second:   {documents_per_second:.1f}")
    print(f"projected 2000:     {projected_2000_seconds:.3f} s")

    # This is intentionally not a timing assertion: execution time depends on
    # the machine and environment. The benchmark is meant for manual profiling.
