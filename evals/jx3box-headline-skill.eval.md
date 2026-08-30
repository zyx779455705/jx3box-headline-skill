# JX3BOX Headline Skill Evaluation

The skill succeeds when its deterministic design brief is structurally valid and conservative, while its creative output preserves article meaning, exact Chinese text, JX3BOX safe-area behavior, and one coherent composition mode.

## Binary criteria

1. `valid-json` — the produced validator output is valid UTF-8 JSON.
2. `supported-canvas` — canvas and centered safe width are exactly one supported JX3BOX pair.
3. `rights-conservative` — no `unknown` or `prohibited` item appears in approved assets, and the output never treats silence as permission.
4. `semantic-title` — an LLM judge confirms the short main title preserves the source article's object and intent, while the subtitle carries omitted detail.
5. `composition-quality` — an LLM judge confirms one primary mode governs hierarchy, direction, subject placement, and effects.
6. `exact-readable-copy` — an LLM judge confirms final Chinese copy is exact, readable at reduced scale, and not generated pseudo-text.

The golden inputs are synthetic coverage cases based on the three user-supplied article workflows. They remain `pending-first-green` until the user accepts a first passing baseline.

```json
{
  "skill": "jx3box-headline-skill",
  "criteria": [
    {
      "id": "valid-json",
      "text": "Produced validator output is valid UTF-8 JSON",
      "type": "command",
      "cmd": "python -c \"import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))\" {output}"
    },
    {
      "id": "supported-canvas",
      "text": "Canvas and centered safe area match a supported JX3BOX pair",
      "type": "command",
      "cmd": "python -c \"import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8')); c=d['canvas']; s=c['safe_area']; assert (c['width'],c['height'],s['x'],s['width']) in [(3200,560,1020,1160),(1600,280,510,580)]\" {output}"
    },
    {
      "id": "rights-conservative",
      "text": "Unknown or prohibited assets are never approved and silence is not permission",
      "type": "command",
      "cmd": "python -c \"import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8')); r=d['rights']; assert r['unknown_rights_are_permission'] is False; assert all(x['rights_status'] not in ('unknown','prohibited') for x in r['approved_assets'])\" {output}"
    },
    {
      "id": "semantic-title",
      "text": "The concise main title preserves the article object and intent; subtitle carries omitted scope without invented claims",
      "type": "llm-judge"
    },
    {
      "id": "composition-quality",
      "text": "One primary composition mode coherently governs hierarchy, motion, subject placement, and effects",
      "type": "llm-judge"
    },
    {
      "id": "exact-readable-copy",
      "text": "Final Chinese copy is exact, readable at 25 percent scale, and contains no generated pseudo-glyphs",
      "type": "llm-judge"
    }
  ],
  "golden": [
    {
      "id": "long-title-compression",
      "input": "golden/long-title-compression/input.json",
      "expected": null,
      "split": "val",
      "expected_status": "pending-first-green"
    },
    {
      "id": "owned-game-screenshot",
      "input": "golden/owned-game-screenshot/input.json",
      "expected": null,
      "split": "val",
      "expected_status": "pending-first-green"
    },
    {
      "id": "unknown-rights-block",
      "input": "golden/unknown-rights-block/input.json",
      "expected": null,
      "split": "val",
      "expected_status": "pending-first-green"
    }
  ]
}
```

