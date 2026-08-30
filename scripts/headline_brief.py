#!/usr/bin/env python3
"""Validate and normalize a JX3BOX headline design brief.

The script enforces supported presets or an explicit custom canvas, safe-area
bounds, conservative image/font rights checks, composition selection, and a
stable QA contract. It produces JSON only; creative bitmap work remains with
the host's image generation or editing tool.

Example:
    python scripts/headline_brief.py --input brief.json --output validated.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


SKILL_NAME = "jx3box-headline-skill"
VERSION = "1.1.0"
MIN_PYTHON = (3, 10)
ALLOWED_RESOLUTIONS = {
    "high": {
        "width": 3200,
        "height": 560,
        "safe_area": {"x": 1020, "y": 0, "width": 1160, "height": 560},
    },
    "standard": {
        "width": 1600,
        "height": 280,
        "safe_area": {"x": 510, "y": 0, "width": 580, "height": 280},
    },
    "compact": {
        "width": 600,
        "height": 200,
        "safe_area": {"x": 90, "y": 16, "width": 420, "height": 168},
    },
}
MIN_CANVAS_EDGE = 64
MAX_CANVAS_EDGE = 16384
ALLOWED_COMPOSITIONS = {"auto", "direct", "flow", "interlock"}
ALLOWED_SUBJECT_POSITIONS = {"left", "center", "right", "both", "none"}
ALLOWED_ATTRIBUTION_PLACEMENTS = {"artwork", "metadata", "readme", "none"}
ALLOWED_INPUT_FIELDS = {
    "article_title",
    "main_title",
    "subtitle",
    "author",
    "resolution",
    "composition_mode",
    "subject_position",
    "layering_requested",
    "commercial_context",
    "notes",
    "font",
    "source_assets",
}
TEXT_INPUT_FIELDS = {
    "article_title",
    "main_title",
    "subtitle",
    "author",
    "composition_mode",
    "subject_position",
    "notes",
}
BOOLEAN_INPUT_FIELDS = {"layering_requested", "commercial_context"}
RIGHTS_ITEM_FIELDS = {
    "id",
    "name",
    "label",
    "creator",
    "source",
    "rights_status",
    "commercial_allowed",
    "attribution",
    "attribution_required",
    "attribution_placement",
}
RIGHTS_TEXT_FIELDS = {
    "id",
    "name",
    "label",
    "creator",
    "source",
    "rights_status",
    "attribution",
    "attribution_placement",
}
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


def _is_integer(value: object) -> bool:
    """Return whether value is an integer but not a boolean."""
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_safe_area(
    raw: object,
    *,
    width: int,
    height: int,
    field: str,
) -> dict[str, int]:
    """Validate and normalize a safe-area rectangle inside a canvas."""
    if not isinstance(raw, dict):
        raise BriefValidationError(
            "Input validation failed",
            [{"field": field, "error": "must be an object with x, y, width, and height"}],
        )
    unknown = sorted(set(raw) - {"x", "y", "width", "height"})
    if unknown:
        raise BriefValidationError(
            "Input validation failed",
            [{"field": field, "error": f"unsupported fields: {', '.join(unknown)}"}],
        )
    values = {key: raw.get(key) for key in ("x", "y", "width", "height")}
    invalid = [key for key, item in values.items() if not _is_integer(item)]
    if invalid:
        raise BriefValidationError(
            "Input validation failed",
            [{"field": f"{field}.{key}", "error": "must be an integer"} for key in invalid],
        )
    safe = {key: int(item) for key, item in values.items()}
    if safe["x"] < 0 or safe["y"] < 0 or safe["width"] <= 0 or safe["height"] <= 0:
        raise BriefValidationError(
            "Input validation failed",
            [{"field": field, "error": "x/y must be non-negative and width/height must be positive"}],
        )
    if safe["x"] + safe["width"] > width or safe["y"] + safe["height"] > height:
        raise BriefValidationError(
            "Input validation failed",
            [{"field": field, "error": "must stay inside the canvas"}],
        )
    return safe


def _normalize_resolution(value: object) -> tuple[str, dict[str, Any]]:
    """Resolve a named preset or an explicit custom canvas specification."""
    if value is None:
        name = "high"
    elif isinstance(value, str):
        name = value.strip().lower()
    elif isinstance(value, dict):
        unknown = sorted(set(value) - {"width", "height", "safe_area"})
        if unknown:
            raise BriefValidationError(
                "Input validation failed",
                [{"field": "resolution", "error": f"unsupported fields: {', '.join(unknown)}"}],
            )
        width = value.get("width")
        height = value.get("height")
        if not _is_integer(width) or not _is_integer(height):
            raise BriefValidationError(
                "Input validation failed",
                [{"field": "resolution", "error": "width and height must be integers"}],
            )
        width = int(width)
        height = int(height)
        if not (MIN_CANVAS_EDGE <= width <= MAX_CANVAS_EDGE):
            raise BriefValidationError(
                "Input validation failed",
                [{"field": "resolution.width", "error": f"must be {MIN_CANVAS_EDGE}-{MAX_CANVAS_EDGE}"}],
            )
        if not (MIN_CANVAS_EDGE <= height <= MAX_CANVAS_EDGE):
            raise BriefValidationError(
                "Input validation failed",
                [{"field": "resolution.height", "error": f"must be {MIN_CANVAS_EDGE}-{MAX_CANVAS_EDGE}"}],
            )
        preset_name = next(
            (
                key
                for key, spec in ALLOWED_RESOLUTIONS.items()
                if spec["width"] == width and spec["height"] == height
            ),
            "",
        )
        if preset_name:
            preset = ALLOWED_RESOLUTIONS[preset_name]
            if "safe_area" in value:
                supplied_safe = _validate_safe_area(
                    value["safe_area"],
                    width=width,
                    height=height,
                    field="resolution.safe_area",
                )
                if supplied_safe != preset["safe_area"]:
                    raise BriefValidationError(
                        "Input validation failed",
                        [{"field": "resolution.safe_area", "error": f"must match the {preset_name} preset"}],
                    )
            return preset_name, {
                "width": width,
                "height": height,
                "safe_area": dict(preset["safe_area"]),
            }
        safe_area = _validate_safe_area(
            value.get("safe_area"),
            width=width,
            height=height,
            field="resolution.safe_area",
        )
        return "custom", {"width": width, "height": height, "safe_area": safe_area}
    else:
        name = ""
    if name not in ALLOWED_RESOLUTIONS:
        raise BriefValidationError(
            "Input validation failed",
            [
                {
                    "field": "resolution",
                    "error": "must be high, standard, compact, or an explicit canvas with safe_area",
                }
            ],
        )
    preset = ALLOWED_RESOLUTIONS[name]
    return name, {
        "width": preset["width"],
        "height": preset["height"],
        "safe_area": dict(preset["safe_area"]),
    }


def _aspect_ratio(width: int, height: int) -> str:
    """Return the reduced integer aspect ratio for a canvas."""
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def _normalize_rights_item(
    raw: object,
    *,
    item_id: str,
    field: str,
    commercial_context: bool,
) -> dict[str, Any]:
    """Normalize and conservatively approve or block one rights record."""
    if not isinstance(raw, dict):
        return {
            "id": item_id,
            "label": field,
            "rights_status": "unknown",
            "approved": False,
            "reason": "rights record must be an object",
            "creator": "",
            "source": "",
            "attribution": "",
            "attribution_required": False,
            "attribution_placement": "none",
            "commercial_allowed": False,
        }

    normalized_id = _text(raw.get("id")) or item_id
    label = _text(raw.get("label")) or _text(raw.get("name")) or field
    status = _text(raw.get("rights_status")).lower() or "unknown"
    creator = _text(raw.get("creator"))
    source = _text(raw.get("source"))
    attribution = _text(raw.get("attribution"))
    commercial_allowed = raw.get("commercial_allowed") is True
    raw_required = raw.get("attribution_required")
    attribution_required = (
        raw_required if isinstance(raw_required, bool) else status in THIRD_PARTY_RIGHTS
    )
    attribution_placement = _text(raw.get("attribution_placement")).lower()
    if not attribution_placement:
        attribution_placement = "metadata" if attribution_required else "none"

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
    if raw_required is not None and not isinstance(raw_required, bool):
        reasons.append("attribution_required must be a boolean")
    if attribution_placement not in ALLOWED_ATTRIBUTION_PLACEMENTS:
        reasons.append(f"unsupported attribution_placement: {attribution_placement}")
        attribution_placement = "metadata"

    if not attribution and status in THIRD_PARTY_RIGHTS and creator and source:
        attribution = f"{creator} · {source}"
    if attribution_required and not attribution:
        reasons.append("required attribution text is missing")
    if attribution_required and attribution_placement == "none":
        reasons.append("required attribution needs artwork, metadata, or readme placement")

    return {
        "id": normalized_id,
        "label": label,
        "rights_status": status,
        "approved": not reasons,
        "reason": "; ".join(reasons) if reasons else "verified for the stated use",
        "creator": creator,
        "source": source,
        "attribution": attribution,
        "attribution_required": attribution_required,
        "attribution_placement": attribution_placement,
        "commercial_allowed": commercial_allowed or status == "public-domain",
    }


def _rights_structure_errors(raw: object, field: str) -> list[dict[str, str]]:
    """Return JSON-Schema-aligned structural errors for a rights record."""
    if not isinstance(raw, dict):
        return [{"field": field, "error": "must be an object"}]
    errors: list[dict[str, str]] = []
    unknown = sorted(set(raw) - RIGHTS_ITEM_FIELDS)
    if unknown:
        errors.append({"field": field, "error": f"unsupported fields: {', '.join(unknown)}"})
    if not (_text(raw.get("name")) or _text(raw.get("label"))):
        errors.append({"field": field, "error": "must include a non-empty name or label"})
    status = _text(raw.get("rights_status")).lower()
    if not status:
        errors.append({"field": f"{field}.rights_status", "error": "is required"})
    elif status not in ALLOWED_RIGHTS:
        errors.append({"field": f"{field}.rights_status", "error": "has an unsupported value"})
    placement = _text(raw.get("attribution_placement")).lower()
    if placement and placement not in ALLOWED_ATTRIBUTION_PLACEMENTS:
        errors.append(
            {"field": f"{field}.attribution_placement", "error": "has an unsupported value"}
        )
    for key in RIGHTS_TEXT_FIELDS:
        if key in raw and not isinstance(raw[key], str):
            errors.append({"field": f"{field}.{key}", "error": "must be a string"})
    for key in ("commercial_allowed", "attribution_required"):
        if key in raw and not isinstance(raw[key], bool):
            errors.append({"field": f"{field}.{key}", "error": "must be a boolean"})
    return errors


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
            "Place exact title copy in the declared safe area.",
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

    unknown_fields = sorted(set(payload) - ALLOWED_INPUT_FIELDS)
    if unknown_fields:
        errors.append(
            {
                "field": "$",
                "error": f"unsupported fields: {', '.join(unknown_fields)}",
            }
        )
    for field in TEXT_INPUT_FIELDS:
        if field in payload and not isinstance(payload[field], str):
            errors.append({"field": field, "error": "must be a string"})
    for field in BOOLEAN_INPUT_FIELDS:
        if field in payload and not isinstance(payload[field], bool):
            errors.append({"field": field, "error": "must be a boolean"})

    raw_assets = payload.get("source_assets", [])
    if not isinstance(raw_assets, list):
        errors.append({"field": "source_assets", "error": "must be an array"})
    else:
        for index, item in enumerate(raw_assets):
            errors.extend(_rights_structure_errors(item, f"source_assets[{index}]"))
    font_raw = payload.get("font")
    if font_raw is not None:
        errors.extend(_rights_structure_errors(font_raw, "font"))

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
    canvas = {
        "name": resolution_name,
        "width": canvas_spec["width"],
        "height": canvas_spec["height"],
        "aspect_ratio": _aspect_ratio(canvas_spec["width"], canvas_spec["height"]),
        "safe_area": dict(canvas_spec["safe_area"]),
    }

    assert isinstance(raw_assets, list)
    assets = [
        _normalize_rights_item(
            item,
            item_id=f"asset-{index + 1}",
            field=f"source_assets[{index}]",
            commercial_context=commercial_context,
        )
        for index, item in enumerate(raw_assets)
    ]
    asset_ids = [item["id"] for item in assets]
    duplicate_ids = sorted({item_id for item_id in asset_ids if asset_ids.count(item_id) > 1})
    if duplicate_ids:
        raise BriefValidationError(
            "Input validation failed",
            [{"field": "source_assets", "error": f"duplicate asset ids: {', '.join(duplicate_ids)}"}],
        )
    approved_assets = [item for item in assets if item["approved"]]
    blocked_assets = [item for item in assets if not item["approved"]]

    if font_raw is None:
        font = _normalize_rights_item(
            {"label": "font", "rights_status": "unknown"},
            item_id="font",
            field="font",
            commercial_context=commercial_context,
        )
        warnings.append("No verified font was supplied; select an open or appropriately licensed font before render.")
    else:
        font = _normalize_rights_item(
            font_raw,
            item_id="font",
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

    attributable_items = [*approved_assets]
    if font["approved"]:
        attributable_items.append(font)
    attribution_records = [
        {
            "id": item["id"],
            "label": item["label"],
            "text": item["attribution"],
            "required": item["attribution_required"],
            "placement": item["attribution_placement"],
        }
        for item in attributable_items
        if item["attribution"]
    ]
    artwork_attribution_lines = [
        record["text"]
        for record in attribution_records
        if record["placement"] == "artwork"
    ]

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
            "hierarchy": ["main_title", "subtitle", "author", "artwork_attribution"],
        },
        "composition": composition,
        "typography": {
            "alignment": "declared safe-area composition with explicit alignment lines",
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
            "artwork_attribution_lines": artwork_attribution_lines,
            "attribution_records": attribution_records,
            "attribution_lines": artwork_attribution_lines,
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
    errors: list[dict[str, str]] = []
    if canvas["aspect_ratio"] != _aspect_ratio(canvas["width"], canvas["height"]):
        errors.append({"field": "canvas", "error": "aspect ratio label is incorrect"})
    if canvas["name"] in ALLOWED_RESOLUTIONS:
        expected = ALLOWED_RESOLUTIONS[canvas["name"]]
        if safe != expected["safe_area"]:
            errors.append({"field": "canvas.safe_area", "error": "preset safe area is incorrect"})
    if (
        safe["x"] < 0
        or safe["y"] < 0
        or safe["x"] + safe["width"] > canvas["width"]
        or safe["y"] + safe["height"] > canvas["height"]
    ):
        errors.append({"field": "canvas.safe_area", "error": "safe area is outside canvas"})
    approved_ids = {item["id"] for item in result["rights"]["approved_assets"]}
    blocked_ids = {item["id"] for item in result["rights"]["blocked_assets"]}
    if approved_ids & blocked_ids:
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
    if sys.version_info < MIN_PYTHON:
        _emit_error(
            RuntimeError(f"Python {'.'.join(map(str, MIN_PYTHON))}+ is required"),
            "runtime",
            "Install a supported Python version and run the command again.",
        )
        return 1
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
