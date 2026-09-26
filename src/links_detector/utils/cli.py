import argparse


def parse_dataset_index(default: int = 0) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "index",
        nargs="?",
        type=int,
        default=default,
        help="Dataset sample index, e.g. 0, 1, 2",
    )
    return parser.parse_args().index
