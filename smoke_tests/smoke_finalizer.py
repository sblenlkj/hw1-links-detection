from links_detector.finalizer import LinksFinalizer


TEXT = """
Согласно пп. 1, 2 и 3 п. 4 и 5 ст. 14 и 15 НК РФ.
Согласно ст. 12.8 КоАП РФ.
Согласно ст. 99 без документа.
Согласно ст. 34 рандомного кодекса.
Согласно ст. 14 и 15 НК РФ.
""".strip()


def main() -> None:
    result = LinksFinalizer().extract(TEXT)

    print("INPUT")
    print("=====")
    print(TEXT)

    print("\nFINAL LINKS")
    print("===========")
    for link in result.links:
        print(link)

    stats = result.stats

    print("\nMETA")
    print("====")
    print(f"total_segments:    {stats.total_segments}")
    print(f"invalid_segments:  {stats.invalid_segments}")
    print(f"resolver_failed:   {stats.resolver_failed}")
    print(f"resolved_segments: {stats.resolved_segments}")
    print(f"expanded_segments: {stats.expanded_segments}")
    print(f"unique_links:      {stats.unique_links}")


if __name__ == "__main__":
    main()
