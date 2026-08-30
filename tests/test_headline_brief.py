#!/usr/bin/env python3
"""Unit tests for the deterministic JX3BOX headline brief validator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from headline_brief import BriefValidationError, build_brief  # noqa: E402


OPEN_FONT = {
    "name": "Open CJK font",
    "rights_status": "open",
    "creator": "Font project",
    "source": "https://example.invalid/font-license",
    "commercial_allowed": True,
    "attribution_required": True,
    "attribution_placement": "metadata",
}


class HeadlineBriefTests(unittest.TestCase):
    """Cover sizes, composition, rights, title limits, and readiness."""

    def test_high_resolution_safe_area(self) -> None:
        result = build_brief(
            {
                "article_title": "明尊入门攻略",
                "main_title": "明尊攻略",
                "font": OPEN_FONT,
            }
        )
        self.assertEqual(result["canvas"]["width"], 3200)
        self.assertEqual(result["canvas"]["height"], 560)
        self.assertEqual(result["canvas"]["safe_area"], {"x": 1020, "y": 0, "width": 1160, "height": 560})

    def test_standard_resolution_safe_area(self) -> None:
        result = build_brief(
            {
                "article_title": "衍天试炼攻略",
                "main_title": "衍天试炼",
                "resolution": {"width": 1600, "height": 280},
                "font": OPEN_FONT,
            }
        )
        self.assertEqual(result["canvas"]["safe_area"], {"x": 510, "y": 0, "width": 580, "height": 280})

    def test_compact_resolution_safe_area(self) -> None:
        result = build_brief(
            {
                "article_title": "九幽副本攻略",
                "main_title": "九幽攻略",
                "resolution": "compact",
                "font": OPEN_FONT,
            }
        )
        self.assertEqual(result["canvas"]["width"], 600)
        self.assertEqual(result["canvas"]["height"], 200)
        self.assertEqual(result["canvas"]["aspect_ratio"], "3:1")
        self.assertEqual(result["canvas"]["safe_area"], {"x": 90, "y": 16, "width": 420, "height": 168})

    def test_custom_resolution_requires_bounded_safe_area(self) -> None:
        result = build_brief(
            {
                "article_title": "自定义横幅",
                "main_title": "自定义",
                "resolution": {
                    "width": 1200,
                    "height": 400,
                    "safe_area": {"x": 180, "y": 40, "width": 840, "height": 320},
                },
                "font": OPEN_FONT,
            }
        )
        self.assertEqual(result["canvas"]["name"], "custom")
        self.assertEqual(result["canvas"]["aspect_ratio"], "3:1")
        self.assertEqual(result["canvas"]["safe_area"]["width"], 840)

        with self.assertRaises(BriefValidationError):
            build_brief(
                {
                    "article_title": "缺少安全区",
                    "main_title": "自定义",
                    "resolution": {"width": 1200, "height": 400},
                    "font": OPEN_FONT,
                }
            )

    def test_owned_asset_is_approved(self) -> None:
        result = build_brief(
            {
                "article_title": "副本增益对比",
                "main_title": "增益对比",
                "font": OPEN_FONT,
                "source_assets": [
                    {
                        "label": "user screenshot",
                        "creator": "user",
                        "source": "conversation attachment",
                        "rights_status": "owned",
                        "commercial_allowed": True,
                    }
                ],
            }
        )
        self.assertTrue(result["ready_for_render"])
        self.assertEqual(result["composition"]["mode"], "direct")
        self.assertEqual(len(result["rights"]["approved_assets"]), 1)

    def test_unknown_asset_is_blocked(self) -> None:
        result = build_brief(
            {
                "article_title": "蓬莱剧情整理",
                "main_title": "蓬莱旧梦",
                "font": OPEN_FONT,
                "source_assets": [
                    {
                        "label": "found illustration",
                        "rights_status": "unknown",
                    }
                ],
            }
        )
        self.assertFalse(result["ready_for_render"])
        self.assertEqual(len(result["rights"]["blocked_assets"]), 1)
        self.assertFalse(result["rights"]["unknown_rights_are_permission"])

    def test_duplicate_labels_use_asset_ids(self) -> None:
        result = build_brief(
            {
                "article_title": "同名素材",
                "main_title": "素材检查",
                "font": OPEN_FONT,
                "source_assets": [
                    {
                        "id": "owned-background",
                        "label": "背景",
                        "rights_status": "owned",
                        "commercial_allowed": True,
                    },
                    {
                        "id": "unknown-background",
                        "label": "背景",
                        "rights_status": "unknown",
                    },
                ],
            }
        )
        self.assertEqual(result["rights"]["approved_assets"][0]["id"], "owned-background")
        self.assertEqual(result["rights"]["blocked_assets"][0]["id"], "unknown-background")

    def test_duplicate_asset_ids_fail(self) -> None:
        with self.assertRaises(BriefValidationError):
            build_brief(
                {
                    "article_title": "重复标识",
                    "main_title": "素材检查",
                    "font": OPEN_FONT,
                    "source_assets": [
                        {"id": "same", "label": "甲", "rights_status": "owned"},
                        {"id": "same", "label": "乙", "rights_status": "owned"},
                    ],
                }
            )

    def test_metadata_font_attribution_is_not_drawn_on_artwork(self) -> None:
        result = build_brief(
            {
                "article_title": "字体署名位置",
                "main_title": "字体检查",
                "font": OPEN_FONT,
            }
        )
        self.assertEqual(result["rights"]["artwork_attribution_lines"], [])
        self.assertEqual(result["rights"]["attribution_records"][0]["placement"], "metadata")

    def test_artwork_attribution_is_explicit(self) -> None:
        result = build_brief(
            {
                "article_title": "素材署名位置",
                "main_title": "署名检查",
                "font": OPEN_FONT,
                "source_assets": [
                    {
                        "id": "licensed-art",
                        "label": "授权插画",
                        "rights_status": "licensed",
                        "creator": "Artist",
                        "source": "https://example.invalid/license",
                        "commercial_allowed": True,
                        "attribution_required": True,
                        "attribution_placement": "artwork",
                    }
                ],
            }
        )
        self.assertEqual(
            result["rights"]["artwork_attribution_lines"],
            ["Artist · https://example.invalid/license"],
        )

    def test_interlock_auto_selection(self) -> None:
        result = build_brief(
            {
                "article_title": "衍天试炼之地攻略",
                "main_title": "衍天试炼",
                "font": OPEN_FONT,
                "subject_position": "left",
                "layering_requested": True,
            }
        )
        self.assertEqual(result["composition"]["mode"], "interlock")
        self.assertIn("right", result["composition"]["title_bias"])

    def test_commercial_rights_must_be_explicit(self) -> None:
        result = build_brief(
            {
                "article_title": "付费资源说明",
                "main_title": "资源指南",
                "commercial_context": True,
                "font": {
                    "name": "Unverified commercial font",
                    "rights_status": "open",
                    "creator": "Font project",
                    "source": "https://example.invalid/font-license",
                    "commercial_allowed": False,
                },
            }
        )
        self.assertFalse(result["ready_for_render"])
        self.assertIn("commercial", result["typography"]["font"]["reason"])

    def test_long_title_warns(self) -> None:
        result = build_brief(
            {
                "article_title": "从入门到进阶的完整明尊攻略",
                "main_title": "从入门到进阶明尊攻略",
                "font": OPEN_FONT,
            }
        )
        self.assertTrue(any("2-8" in warning for warning in result["_warnings"]))

    def test_title_over_twenty_units_fails(self) -> None:
        with self.assertRaises(BriefValidationError):
            build_brief(
                {
                    "article_title": "很长的文章标题",
                    "main_title": "明尊" * 11,
                    "font": OPEN_FONT,
                }
            )

    def test_unknown_input_field_fails(self) -> None:
        with self.assertRaises(BriefValidationError):
            build_brief(
                {
                    "article_title": "未知字段",
                    "main_title": "字段检查",
                    "font": OPEN_FONT,
                    "resoultion": "compact",
                }
            )

    def test_unknown_rights_field_fails(self) -> None:
        with self.assertRaises(BriefValidationError):
            build_brief(
                {
                    "article_title": "未知素材字段",
                    "main_title": "字段检查",
                    "font": {**OPEN_FONT, "license_note": "unexpected"},
                }
            )

    def test_wrong_optional_type_fails(self) -> None:
        with self.assertRaises(BriefValidationError):
            build_brief(
                {
                    "article_title": "类型检查",
                    "main_title": "类型检查",
                    "subtitle": 123,
                    "font": OPEN_FONT,
                }
            )

    def test_missing_rights_status_fails(self) -> None:
        with self.assertRaises(BriefValidationError):
            build_brief(
                {
                    "article_title": "授权字段",
                    "main_title": "授权检查",
                    "font": {"name": "Missing status"},
                }
            )


if __name__ == "__main__":
    unittest.main()
