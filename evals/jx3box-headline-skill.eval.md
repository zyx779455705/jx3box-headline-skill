# JX3BOX Headline Skill Evaluation

The skill succeeds when its deterministic design brief is structurally valid and conservative, while its creative output preserves article meaning, exact Chinese text, JX3BOX safe-area behavior, and one coherent composition mode.

## Binary criteria

1. `valid-json` — the produced validator output is valid UTF-8 JSON.
2. `supported-canvas` — canvas and centered safe width are exactly one supported JX3BOX pair.
3. `rights-conservative` — no `unknown` or `prohibited` item appears in approved assets, and the output never treats silence as permission.
4. `golden-baseline` — rollout output is JSON-equal to the accepted deterministic baseline (enforced by `run_evals.py --rollout`).
5. `semantic-title` — an LLM judge confirms the short main title preserves the source article's object and intent, while the subtitle carries omitted detail.
6. `composition-quality` — an LLM judge confirms one primary mode governs hierarchy, direction, subject placement, and effects.
7. `exact-readable-copy` — an LLM judge confirms final Chinese copy is exact, readable at reduced scale, and not generated pseudo-text.

The golden inputs are synthetic coverage cases based on the three user-supplied article workflows. The deterministic validator outputs are committed baselines; creative bitmap quality remains an explicit LLM/human review step.

```json
{
  "skill": "jx3box-headline-skill",
  "run": "python scripts/headline_brief.py --input {input} --output {output}",
  "criteria": [
    {
      "id": "valid-json",
      "text": "Produced validator output is valid UTF-8 JSON",
      "type": "command",
      "cmd": "python -c \"import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))\" {output}"
    },
    {
      "id": "supported-canvas",
      "text": "Canvas dimensions, aspect label, and safe area are internally valid",
      "type": "command",
      "cmd": "python -c \"import json,sys,math; d=json.load(open(sys.argv[1], encoding='utf-8')); c=d['canvas']; s=c['safe_area']; g=math.gcd(c['width'],c['height']); assert c['aspect_ratio']==f'{c[\\\"width\\\"]//g}:{c[\\\"height\\\"]//g}' and s['x']>=0 and s['y']>=0 and s['width']>0 and s['height']>0 and s['x']+s['width']<=c['width'] and s['y']+s['height']<=c['height']\" {output}"
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
      "expected": "golden/long-title-compression/expected.json",
      "split": "val",
      "expected_status": "accepted"
    },
    {
      "id": "owned-game-screenshot",
      "input": "golden/owned-game-screenshot/input.json",
      "expected": "golden/owned-game-screenshot/expected.json",
      "split": "val",
      "expected_status": "accepted"
    },
    {
      "id": "unknown-rights-block",
      "input": "golden/unknown-rights-block/input.json",
      "expected": "golden/unknown-rights-block/expected.json",
      "split": "val",
      "expected_status": "accepted"
    }
  ]
}
```
