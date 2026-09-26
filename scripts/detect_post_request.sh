curl -s -X POST "http://localhost:8978/detect" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --rawfile text dataset/markdown/00_readme_example.md \
    '{text: $text}')" \
  | jq