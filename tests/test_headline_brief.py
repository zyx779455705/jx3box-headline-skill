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


if __name__ == "__main__":
    unittest.main()

