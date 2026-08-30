# jx3box-headline-skill

> 为剑网3魔盒 JX3BOX 文章制作、修改和审查 3200×560 或 1600×280 头条图。

## Purpose

本技能把文章主题转化为可发布的魔盒头条：压缩主标题、安排副标题与作者、核验图片和字体授权、选择构图模式、制作或编辑视觉，并按中心安全区和缩放可读性复核成品。规则来自 JX3BOX 的文字篇、图片篇和技巧篇教程。

## Activation

当用户明确提到 JX3BOX、剑网3魔盒、文章头条、攻略封面、3200×560、1600×280、魔盒横幅或现有魔盒头条改稿时启用。支持 `/jx3box-headline-skill`，也可自然语言触发。

示例：

- “给这篇明尊入门攻略做一张魔盒头条。”
- “用我的游戏截图做 3200×560 的 JX3BOX 封面。”
- “检查这张头条的中心安全区、字体授权和可读性。”

不要因为普通海报、头像、直播封面或通用字体问题自动启用。

## Usage

1. 读取 `SKILL.md` 和 `references/article-derived-rules.md`。
2. 从用户输入提取主题、标题、作者、素材来源、商业性质和输出尺寸。
3. 使用 `scripts/headline_brief.py` 校验版权、安全区和构图简报。
4. 位图生成/编辑使用宿主图像工具；精确中文字不要交给生成模型直接渲染。
5. 交付成品、标题文案、构图说明、授权说明和 QA 结果。

## Files

- `SKILL.md` — 完整技能定义和工作流
- `scripts/headline_brief.py` — 设计简报、版权与安全区校验
- `references/` — 文章规则、执行指南和故障排查
- `assets/` — JSON Schema 与 QA 清单
- `evals/` — 二进制评测标准和黄金用例
- `jx3box-headline-skill` / `jx3box-headline-skill.ps1` — 跨平台简报校验器启动脚本
