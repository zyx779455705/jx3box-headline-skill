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

Rights records use stable asset IDs so two different files may share a human label without colliding. Attribution is recorded separately from its placement: only licenses requiring `artwork` attribution consume banner space; `metadata` and `readme` attribution remain in delivery records.

## Canvas extension

The tutorials' official presets remain 3200×560 and 1600×280. Version 1.1.0 adds the user-requested 600×200 compact preset with a declared 420×168 safe area. Arbitrary dimensions are accepted only with an explicit in-bounds safe-area rectangle, because the 40:7 crop assumptions cannot be inferred for other aspect ratios.

Version 1.1.1 makes 1600×280 the default output. The 3200×560 high preset is selected only when the user explicitly requests high resolution or that exact size; compact and custom dimensions also remain explicit choices.

Version 1.3.0 supersedes the physical-output part of that decision: user dimensions are now treated as 1× logical display sizes and delivered at `@2x` by default. Thus logical 1600×280 produces 3200×560, logical 600×200 produces 1200×400, and custom canvases and safe areas are doubled consistently. Only an explicit 1× or exact-physical-pixel request disables the multiplier. The skill exports only the `@2x` set by default and rejects ordinary interpolation enlargement as fake high-resolution output.

Version 1.4.0 supersedes the sizing semantics from 1.3.0. Every stated width and height now means the final file's exact physical pixels, with no implicit multiplier. Omitted dimensions default to 3200×560; explicit 1600×280, 600×200, or custom dimensions are delivered exactly as written. Terms such as `@2x`, Retina, or high resolution do not override an explicit pixel size. The source-quality rule remains: low-resolution finished art must not be enlarged with ordinary interpolation and presented as genuinely detailed output.

## Image-tool boundary

The creative workflow is intentionally not reduced to a fake deterministic renderer. The host's image generation/editing capability produces or edits the bitmap. Exact Chinese text is placed with a deterministic editor or vector/canvas tool after background generation. Brief, safe-area, rights, and QA checks are kept as concise skill instructions rather than a bundled runtime.

## Artifact assessment

The agent-skill-creator artifact detector returned `None`. The requested output is a bitmap headline, not a time series, comparison chart, KPI panel, or data table, so no React artifact template is embedded.

## Distribution

The repository contains only the skill instructions and supporting references. Users clone it directly into their host's native skill directory; no installer, validator runtime, or CI package is bundled.
