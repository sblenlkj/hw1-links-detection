# Gold annotations

Expected outputs for files from `dataset/markdown/`.

Naming convention:

```text
dataset/markdown/00_readme_example.md
dataset/gold/00_readme_example.jsonl
```

Each non-empty line in a gold file is one final `LawLink` JSON object:

```json
{"law_id": 15, "article": "374", "point_article": "1", "subpoint_article": "1"}
{"law_id": 13, "article": "105", "point_article": null, "subpoint_article": null}
```

`DatasetLoader` automatically deserializes the JSONL file into
`list[LawLink]` and exposes it as `DatasetSample.expected`.

For list-valued subpoints, one textual reference is expanded into multiple
`LawLink` rows, following the homework README example.
