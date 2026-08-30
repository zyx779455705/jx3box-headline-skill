#!/usr/bin/env python3
"""Validate and normalize a JX3BOX headline design brief.

The script enforces the two supported canvas sizes, centered safe widths,
conservative image/font rights checks, composition selection, and a stable QA
contract. It produces JSON only; creative bitmap work remains with the host's
image generation or editing tool.

Example:
    python scripts/headline_brief.py --input brief.json --output validated.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SKILL_NAME = "jx3box-headline-skill"
VERSION = "1.0.0"
MIN_PYTHON = (3, 10)
ALLOWED_RESOLUTIONS = {
    "high": {"width": 3200, "height": 560, "safe_width": 1160},
    "standard": {"width": 1600, "height": 280, "safe_width": 580},
}
ALLOWED_COMPOSITIONS = {"auto", "direct", "flow", "interlock"}
ALLOWED_SUBJECT_POSITIONS = {"left", "center", "right", "both", "none"}
ALLOWED_RIGHTS = {
    "owned",
    "explicit-permission",
    "licensed",
    "open",
    "public-domain",
    "unknown",
    "prohibited",
}
APPROVABLE_RIGHTS = {
    "owned",
    "explicit-permission",
    "licensed",
    "open",
    "public-domain",
}
THIRD_PARTY_RIGHTS = {"explicit-permission", "licensed", "open"}


class BriefValidationError(Exception):
    """Represent one or more user-correctable brief errors.

    Args:
        message: Human-readable summary.
        details: Field-level error records.

    Example:
        >>> BriefValidationError("Invalid", [{"field": "main_title", "error": "empty"}])
        BriefValidationError('Invalid')
    """

    def __init__(self, message: str, details: list[dict[str, str]]) -> None:
        super().__init__(message)
        self.details = details


def _text(value: object) -> str:
    """Return a stripped text value without accepting structured objects."""
    if value is None:
        return ""
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())


def display_units(text: str) -> int:
    """Count non-whitespace Unicode code points used by headline copy.

    Args:
        text: Candidate title or subtitle.

    Returns:
        Number of visible non-whitespace code points.

    Example:
        >>> display_units("明尊 攻略")
        4
    """
    return sum(1 for char in text if not char.isspace())


def load_input(path: Path) -> dict[str, Any]:
    """Load one UTF-8 JSON input object.

    Args:
        path: JSON file path.

    Returns:
        Parsed object.

    Raises:
        BriefValidationError: If the path is unreadable, JSON is invalid, or
            the top-level value is not an object.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BriefValidationError(
            "Unable to read input",
            [{"field": "input", "error": str(exc)}],
        ) from exc
    except json.JSONDecodeError as exc:
        raise BriefValidationError(
            "Input is not valid JSON",
            [{"field": "input", "error": f"line {exc.lineno}: {exc.msg}"}],
        ) from exc
    if not isinstance(payload, dict):
        raise BriefValidationError(
            "Input validation failed",
            [{"field": "$", "error": "top-level JSON value must be an object"}],
        )
    return payload


def _normalize_resolution(value: object) -> tuple[str, dict[str, int]]:
    """Resolve a named or explicit supported canvas specification."""
    if value is None:
        name = "high"
    elif isinstance(value, str):
        name = value.strip().lower()
    elif isinstance(value, dict):
        width = value.get("width")
        height = value.get("height")
        name = next(
            (
                key
                for key, spec in ALLOWED_RESOLUTIONS.items()
                if spec["width"] == width and spec["height"] == height
            ),
            "",
        )
    else:
        name = ""
    if name not in ALLOWED_RESOLUTIONS:
        raise BriefValidationError(
            "Input validation failed",
            [
                {
                    "field": "resolution",
                    "error": "must be high, standard, 3200x560, or 1600x280",
                }
            ],
        )
    return name, dict(ALLOWED_RESOLUTIONS[name])


def _normalize_rights_item(
    raw: object,
    *,
    field: str,
    commercial_context: bool,
) -> dict[str, Any]:
    """Normalize and conservatively approve or block one rights record."""
    if not isinstance(raw, dict):
        return {
            "label": field,
            "rights_status": "unknown",
            "approved": False,
            "reason": "rights record must be an object",
            "creator": "",
            "source": "",
            "attribution": "",
            "commercial_allowed": False,
        }

    label = _text(raw.get("label")) or _text(raw.get("name")) or field
    status = _text(raw.get("rights_status")).lower() or "unknown"
    creator = _text(raw.get("creator"))
    source = _text(raw.get("source"))
    attribution = _text(raw.get("attribution"))
    commercial_allowed = raw.get("commercial_allowed") is True

    reasons: list[str] = []
    if status not in ALLOWED_RIGHTS:
        reasons.append(f"unsupported rights_status: {status}")
        status = "unknown"
    if status not in APPROVABLE_RIGHTS:
        reasons.append("rights are unknown or explicitly prohibited")
    if status in THIRD_PARTY_RIGHTS and (not creator or not source):
        reasons.append("third-party material needs both creator and source")
    if status == "public-domain" and not source:
        reasons.append("public-domain claim needs a source")
    if commercial_context and status != "public-domain" and not commercial_allowed:
        reasons.append("commercial use is not explicitly allowed")

    if not attribution and status in THIRD_PARTY_RIGHTS and creator and source:
        attribution = f"{creator} · {source}"

    return {
        "label": label,
        "rights_status": status,
        "approved": not reasons,
        "reason": "; ".join(reasons) if reasons else "verified for the stated use",
        "creator": creator,
        "source": source,
        "attribution": attribution,
        "commercial_allowed": commercial_allowed or status == "public-domain",
    }


def _select_composition(
    requested: str,
    *,
    subject_position: str,
    layering_requested: bool,
    approved_asset_count: int,
) -> tuple[str, str]:
    """Choose one primary composition mode and explain the decision."""
    if requested != "auto":
        explanations = {
            "direct": "User selected a strong-background direct text composition.",
            "flow": "User selected a shape-and-line composition with one motion direction.",
            "interlock": "User selected foreground/background interlocking between subject and title.",
        }
        return requested, explanations[requested]
    if layering_requested and subject_position != "none":
        return "interlock", "A visible subject and requested layering support text/subject interlocking."
    if approved_asset_count:
        return "direct", "Verified source material can carry a direct text-on-image composition."
    return "flow", "No approved source image is required; build an original directional material background."


def _composition_plan(mode: str, subject_position: str) -> dict[str, Any]:
    """Return mode-specific actions and a safe title bias."""
    plans: dict[str, list[str]] = {
        "direct": [
            "Place exact title copy in the centered safe area.",
            "Adjust local background brightness before adding text effects.",
            "Use shadow, stroke, glow, or gradient only when contrast still needs help.",
        ],
        "flow": [
            "Choose one dominant diagonal or horizontal motion direction.",
            "Keep secondary lines and arrows lower contrast than the title.",
            "Allow denser detail at the edges while keeping the center clean.",
        ],
        "interlock": [
            "Build separate background-title, subject, and foreground-title layers.",
            "Let the subject or weapon cross only non-critical title strokes.",
            "Use restrained shadow or glow to preserve readable depth.",
        ],
    }
    bias = {
        "left": "bias title to the right half of the safe area",
        "right": "bias title to the left half of the safe area",
        "both": "keep title centered between edge subjects",
        "center": "move or crop the subject away from exact title copy",
        "none": "keep title centered",
    }[subject_position]
    return {"mode": mode, "title_bias": bias, "actions": plans[mode]}


def _load_qa_checks() -> list[dict[str, Any]]:
    """Load the package's machine-readable QA checklist."""
    path = Path(__file__).resolve().parent.parent / "assets" / "qa-checklist.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to load QA checklist: {exc}") from exc
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        raise RuntimeError("QA checklist has no checks")
    return checks


def build_brief(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate input and build the normalized JX3BOX headline brief.

    Args:
        payload: User-facing JSON object described in `assets/brief.schema.json`.

    Returns:
        JSON-serializable validated brief, rights gate, and QA checklist.

    Raises:
        BriefValidationError: If required content, enum values, or title limits
            are invalid.
        RuntimeError: If package assets are missing or malformed.

    Example:
        >>> result = build_brief({"article_title": "明尊教程", "main_title": "明尊攻略"})
        >>> result["canvas"]["width"]
        3200
    """
    errors: list[dict[str, str]] = []
    warnings: list[str] = []

    article_title = _text(payload.get("article_title"))
    main_title = _text(payload.get("main_title"))
    subtitle = _text(payload.get("subtitle"))
    author = _text(payload.get("author"))
    notes = _text(payload.get("notes"))
    commercial_context = payload.get("commercial_context") is True

    if not article_title:
        errors.append({"field": "article_title", "error": "must not be empty"})
    if not main_title:
        errors.append({"field": "main_title", "error": "must not be empty"})
    title_units = display_units(main_title)
    if title_units > 20:
        errors.append({"field": "main_title", "error": "must be 20 visible characters or fewer"})
    elif title_units > 8:
        warnings.append("Main title exceeds the usual 2-8 Chinese-character target; shorten or split it.")
    if article_title and article_title != main_title and not subtitle:
        warnings.append("Subtitle is empty; consider moving omitted scope or promise from the long title into it.")

    requested_mode = _text(payload.get("composition_mode")).lower() or "auto"
    if requested_mode not in ALLOWED_COMPOSITIONS:
        errors.append(
            {
                "field": "composition_mode",
                "error": "must be auto, direct, flow, or interlock",
            }
        )
    subject_position = _text(payload.get("subject_position")).lower() or "none"
    if subject_position not in ALLOWED_SUBJECT_POSITIONS:
        errors.append(
            {
                "field": "subject_position",
                "error": "must be left, center, right, both, or none",
            }
        )

    if errors:
        raise BriefValidationError("Input validation failed", errors)

    resolution_name, canvas_spec = _normalize_resolution(payload.get("resolution"))
    safe_x = (canvas_spec["width"] - canvas_spec["safe_width"]) // 2
    canvas = {
        "name": resolution_name,
        "width": canvas_spec["width"],
        "height": canvas_spec["height"],
        "aspect_ratio": "40:7",
        "safe_area": {
            "x": safe_x,
            "y": 0,
            "width": canvas_spec["safe_width"],
            "height": canvas_spec["height"],
        },
    }

    raw_assets = payload.get("source_assets", [])
    if not isinstance(raw_assets, list):
        raise BriefValidationError(
            "Input validation failed",
            [{"field": "source_assets", "error": "must be an array"}],
        )
    assets = [
        _normalize_rights_item(
            item,
            field=f"source_assets[{index}]",
            commercial_context=commercial_context,
        )
        for index, item in enumerate(raw_assets)
    ]
    approved_assets = [item for item in assets if item["approved"]]
    blocked_assets = [item for item in assets if not item["approved"]]

    font_raw = payload.get("font")
    if font_raw is None:
        font = _normalize_rights_item(
            {"label": "font", "rights_status": "unknown"},
            field="font",
            commercial_context=commercial_context,
        )
        warnings.append("No verified font was supplied; select an open or appropriately licensed font before render.")
    else:
        font = _normalize_rights_item(
            font_raw,
            field="font",
            commercial_context=commercial_context,
        )

    if blocked_assets:
        warnings.append("One or more source assets are blocked; replace them before generating the final headline.")
    if not font["approved"]:
        warnings.append("Font rights are not ready for the stated use.")
    if subject_position == "center":
        warnings.append("A centered subject conflicts with the title safe area; move/crop it or use edge subjects.")

    mode, rationale = _select_composition(
        requested_mode,
        subject_position=subject_position,
        layering_requested=payload.get("layering_requested") is True,
        approved_asset_count=len(approved_assets),
    )
    composition = _composition_plan(mode, subject_position)
    composition["rationale"] = rationale

    attribution_lines = [
        item["attribution"]
        for item in approved_assets
        if item["attribution"]
    ]
    if font["approved"] and font["attribution"]:
        attribution_lines.append(font["attribution"])

    ready_for_render = not blocked_assets and font["approved"]
    result = {
        "skill": SKILL_NAME,
        "version": VERSION,
        "ready_for_render": ready_for_render,
        "canvas": canvas,
        "copy": {
            "article_title": article_title,
            "main_title": main_title,
            "main_title_units": title_units,
            "subtitle": subtitle,
            "author": author,
            "hierarchy": ["main_title", "subtitle", "author", "attribution"],
        },
        "composition": composition,
        "typography": {
            "alignment": "centered safe-area composition with explicit alignment lines",
            "exact_text_required": True,
            "model_generated_final_chinese_text_allowed": False,
            "font": font,
            "contrast_sequence": [
                "test black or white title",
                "adjust local background brightness",
                "add restrained shadow/stroke/glow if still needed",
            ],
        },
        "rights": {
            "commercial_context": commercial_context,
            "approved_assets": approved_assets,
            "blocked_assets": blocked_assets,
            "attribution_lines": attribution_lines,
            "unknown_rights_are_permission": False,
        },
        "asset_strategy": (
            "use-approved-assets" if approved_assets else "generate-original-no-text-background"
        ),
        "notes": notes,
        "qa_checklist": _load_qa_checks(),
        "_warnings": warnings,
    }
    _sanity_check(result)
    return result


def _sanity_check(result: dict[str, Any]) -> None:
    """Reject impossible validator output before it reaches an image workflow."""
    canvas = result["canvas"]
    safe = canvas["safe_area"]
    expected = ALLOWED_RESOLUTIONS[canvas["name"]]
    errors: list[dict[str, str]] = []
    if canvas["width"] * 7 != canvas["height"] * 40:
        errors.append({"field": "canvas", "error": "aspect ratio drifted from 40:7"})
    if safe["width"] != expected["safe_width"]:
        errors.append({"field": "canvas.safe_area.width", "error": "safe width is incorrect"})
    if safe["x"] < 0 or safe["x"] + safe["width"] > canvas["width"]:
        errors.append({"field": "canvas.safe_area", "error": "safe area is outside canvas"})
    approved_labels = {item["label"] for item in result["rights"]["approved_assets"]}
    blocked_labels = {item["label"] for item in result["rights"]["blocked_assets"]}
    if approved_labels & blocked_labels:
        errors.append({"field": "rights", "error": "an asset cannot be both approved and blocked"})
    if errors:
        raise RuntimeError(json.dumps(errors, ensure_ascii=False))


def check_prerequisites() -> dict[str, Any]:
    """Return machine-readable runtime readiness without exposing secrets."""
    skill_root = Path(__file__).resolve().parent.parent
    checks = [
        {
            "check": "python",
            "required": ".".join(map(str, MIN_PYTHON)),
            "found": platform_python_version(),
            "ok": sys.version_info >= MIN_PYTHON,
        },
        {
            "check": "qa-checklist",
            "required": "assets/qa-checklist.json",
            "found": str(skill_root / "assets" / "qa-checklist.json"),
            "ok": (skill_root / "assets" / "qa-checklist.json").is_file(),
        },
        {
            "check": "api-key",
            "required": "none",
            "found": "not required",
            "ok": True,
        },
        {
            "check": "network",
            "required": "none for validator",
            "found": "not tested",
            "ok": True,
        },
    ]
    return {"ready": all(item["ok"] for item in checks), "checks": checks}


def platform_python_version() -> str:
    """Return the active Python version for diagnostics."""
    return ".".join(str(part) for part in sys.version_info[:3])


def diagnostics() -> dict[str, Any]:
    """Return supported commands and harness capabilities."""
    return {
        "skill": SKILL_NAME,
        "version": VERSION,
        "harness_level": "creative-workflow-with-deterministic-brief-validation",
        "commands": [
            "--input <brief.json> --output <validated.json>",
            "--check-prereqs",
            "--diagnostics",
        ],
        "harness_features": {
            "input_validation": True,
            "output_sanity": True,
            "rights_gate": True,
            "structured_errors": True,
            "image_generation": False,
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write UTF-8 JSON, creating only the requested parent directory."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(f"Unable to write output: {exc}") from exc


def _emit_error(error: Exception, error_type: str, hint: str) -> None:
    """Print one structured error object to stderr."""
    payload: dict[str, Any] = {
        "error": str(error),
        "error_type": error_type,
        "hint": hint,
    }
    if isinstance(error, BriefValidationError):
        payload["details"] = error.details
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)


def main() -> int:
    """Run the validator CLI and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="UTF-8 JSON design brief")
    parser.add_argument("--output", type=Path, help="Validated JSON output path")
    parser.add_argument("--check-prereqs", action="store_true")
    parser.add_argument("--diagnostics", action="store_true")
    args = parser.parse_args()

    try:
        if args.check_prereqs:
            print(json.dumps(check_prerequisites(), ensure_ascii=False, indent=2))
            return 0
        if args.diagnostics:
            print(json.dumps(diagnostics(), ensure_ascii=False, indent=2))
            return 0
        if args.input is None or args.output is None:
            raise BriefValidationError(
                "Input validation failed",
                [
                    {
                        "field": "arguments",
                        "error": "--input and --output are required for validation",
                    }
                ],
            )
        result = build_brief(load_input(args.input))
        _write_json(args.output, result)
        print(json.dumps({"ok": True, "output": str(args.output)}, ensure_ascii=False))
        return 0
    except BriefValidationError as exc:
        _emit_error(exc, "validation", "Fix the listed fields and run the validator again.")
        return 1
    except RuntimeError as exc:
        _emit_error(exc, "runtime", "Verify the skill package is complete and the output path is writable.")
        return 1
    except OSError as exc:
        _emit_error(exc, "runtime", "Verify the requested files and permissions.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
