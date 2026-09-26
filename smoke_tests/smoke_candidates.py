from links_detector.finalizer import LinksFinalizer
from links_detector.utils import dataset, parse_dataset_index


def main() -> None:
    sample = dataset.load(parse_dataset_index())
    result = LinksFinalizer().extract(sample.text)

    print(f"Input: {sample.path.name}")
    print(f"Characters: {len(sample.text)}")

    stats = result.stats
    print("\nMETA")
    print("====")
    print(f"total_segments:    {stats.total_segments}")
    print(f"invalid_segments:  {stats.invalid_segments}")
    print(f"resolver_failed:   {stats.resolver_failed}")
    print(f"resolved_segments: {stats.resolved_segments}")
    print(f"ambiguous_segments:{stats.ambiguous_segments:>4}")
    print(f"expanded_segments: {stats.expanded_segments}")
    print(f"produced_links:    {stats.produced_links}")
    print(f"unique_links:      {stats.unique_links}")

    print("\nSEGMENTS")
    print("========")
    for index, resolution in enumerate(result.resolutions, start=1):
        segment = resolution.segment
        print(
            f"[{index:02d}] valid={segment.valid} "
            f"span=({segment.start}, {segment.end}) "
            f"next_start={segment.next_start}"
        )
        for match in segment.matches:
            print(f"     {type(match).__name__}: {match}")

        if not segment.valid:
            print("     resolve: SKIPPED (invalid segment)")
        elif not resolution.resolved:
            print("     resolve: FAILED")
        elif len(resolution.resolved) == 1:
            resolved = resolution.resolved[0]
            print(
                f"     resolve: law_id={resolved.law_id} "
                f"family={resolved.family}"
            )
        else:
            candidates = ", ".join(
                str(resolved.law_id) for resolved in resolution.resolved
            )
            print(f"     resolve: AMBIGUOUS candidates={candidates}")
        print()

    print("\nFOUND")
    print("=====")
    for link in result.links:
        print(link)

    if sample.expected is None:
        print("\nGOLD")
        print("====")
        print("No gold annotations for this dataset sample.")
        return

    found = set(result.links)
    expected = set(sample.expected)

    matched = expected & found
    missing = expected - found
    unexpected = found - expected

    print("\nGOLD COMPARISON")
    print("===============")
    print(f"expected:   {len(expected)}")
    print(f"matched:    {len(matched)}")
    print(f"missing:    {len(missing)}")
    print(f"unexpected: {len(unexpected)}")

    if missing:
        print("\nMISSING")
        print("=======")
        for link in sorted(
            missing,
            key=lambda item: (
                item.law_id,
                item.article or "",
                item.point_article or "",
                item.subpoint_article or "",
            ),
        ):
            print(link)

    if unexpected:
        print("\nUNEXPECTED")
        print("==========")
        for link in sorted(
            unexpected,
            key=lambda item: (
                item.law_id,
                item.article or "",
                item.point_article or "",
                item.subpoint_article or "",
            ),
        ):
            print(link)


if __name__ == "__main__":
    main()
