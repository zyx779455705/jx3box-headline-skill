# Architecture and Content Decisions

## Skill shape

`jx3box-headline-skill` is a simple, single-domain skill. Copywriting, rights review, composition, image creation, typography, and QA are tightly coupled parts of one JX3BOX headline workflow, so splitting them into independently activated sub-skills would add routing without useful separation.

## Source decision

The three user-supplied JX3BOX community articles are the primary design specification:

- Community 609: title compression, font licensing, exact banner sizes, center safe width, alignment, hierarchy, and font modification.
- Community 607: image rights, attribution, direct composition, shape/flow composition, and subject/text interlocking.
- Community 608: iterative refinements for spacing, shortening, layering, contrast, subtitle treatment, subject avoidance, shadows, transparency, English texture, and directional blur.

The skill does not depend on a scraping API at runtime. Article URLs are declared as review dependencies, while all operational rules needed for a run are stored locally in `references/article-derived-rules.md`.

## Copyright boundary

The original image article treats the absence of an explicit prohibition as potentially usable with attribution. This skill uses a stricter rule: silence is not permission. Third-party assets require ownership, an explicit license, explicit permission, or public-domain status. Unknown rights are blocked and replaced with user-owned screenshots or newly generated material.

## Image-tool boundary

The creative workflow is intentionally not reduced to a fake deterministic renderer. The host's image generation/editing capability produces or edits the bitmap. The bundled Python script validates the brief, safe area, rights record, and QA contract only. Exact Chinese text is placed with a deterministic editor or vector/canvas tool after background generation.

## Artifact assessment

The agent-skill-creator artifact detector returned `None`. The requested output is a bitmap headline, not a time series, comparison chart, KPI panel, or data table, so no React artifact template is embedded.

## Evaluation strategy

Five independent checks define success: valid structured output, exact supported canvas and safe area, conservative asset approval, semantically faithful title hierarchy, and composition/legibility quality. Three golden inputs cover a long guide title, a user-owned screenshot, and an unknown-rights illustration. The creative end-to-end image workflow has no deterministic `run` command; the brief validator is covered by unit tests.

