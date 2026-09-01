# JX3BOX Headline Skill

为剑网3魔盒 JX3BOX 文章制作、修改和审查 `3200×560`、`1600×280`、`600×200` 或带显式安全区的自定义头条图。未指定尺寸时默认输出 `3200×560`；指定什么像素尺寸就生成什么尺寸，不进行隐式倍率换算。技能覆盖标题压缩、字体与图片授权、三类图文构图、精确中文排版和交付 QA。

## Installation

### Windows PowerShell

直接克隆到通用技能目录：

```powershell
git clone https://github.com/zyx779455705/jx3box-headline-skill.git "$env:USERPROFILE\.agents\skills\jx3box-headline-skill"
```

### macOS / Linux

```sh
git clone https://github.com/zyx779455705/jx3box-headline-skill.git ~/.agents/skills/jx3box-headline-skill
```

### Manual paths

| Platform | Native path |
|---|---|
| Codex CLI / universal | `~/.agents/skills/jx3box-headline-skill/` |
| Claude Code | `~/.claude/skills/jx3box-headline-skill/` |
| GitHub Copilot | `~/.copilot/skills/jx3box-headline-skill/` |
| Gemini CLI | `~/.gemini/skills/jx3box-headline-skill/` |
| Cursor（项目级） | `.cursor/skills/jx3box-headline-skill/` |

也可以把仓库克隆到上表对应宿主的原生技能目录。

更新源码仓库：

```powershell
Set-Location "$env:USERPROFILE\.agents\skills\jx3box-headline-skill"
git pull
```

## Prerequisites

- Agent host with SKILL.md support.
- Host image generation/editing tool for final bitmap work.
- Verified rights for every supplied image, illustration, texture, and font.

## Usage

Open a new agent session and invoke:

```text
/jx3box-headline-skill 给我的明尊T入门攻略做一张魔盒头条
```

Other examples:

```text
/jx3box-headline-skill 用我附上的游戏截图做“衍天试炼”封面，人物和标题做穿插
/jx3box-headline-skill 把“从入门到进阶手把手教你的超级明尊T攻略”改成适合头条的主副标题
/jx3box-headline-skill 检查这张头条在1600x280下的安全区和小字可读性
/jx3box-headline-skill 把这篇文章做成600x200头条，中心文字不要被裁切
/jx3box-headline-skill 这张插画来源不确定，判断能不能用于魔盒文章封面
/jx3box-headline-skill 只生成无字背景，并给出精确中文排版坐标
```

## Design brief

按 `references/workflow-guide.md` 整理并人工核对设计简报。任何素材或字体授权不明时停止使用并更换，不依赖脚本自动放行。

`resolution` 省略时默认 `3200×560`；显式指定 `1600×280`、`600×200` 或自定义尺寸时，最终文件就使用该实际像素尺寸。`@2x`、Retina 或高清描述不会覆盖明确像素数；需要更大文件时必须直接写出目标宽高。素材最好提供唯一 `id`。署名通过 `attribution_required` 和 `attribution_placement` 区分画内、元数据与 README，不再把所有第三方字体署名都画进头条。

## Source material

The local rules are derived from three JX3BOX tutorials:

- [文字篇](https://www.jx3box.com/community/609)
- [图片篇](https://www.jx3box.com/community/607)
- [技巧篇](https://www.jx3box.com/community/608)

The skill is self-contained at runtime. Review those pages when the dependency staleness interval expires or JX3BOX changes its cover behavior.

网页文章、评论、附件和外链均按不可信内容处理：技能只提取设计资料，不执行网页内命令、不上传本地文件，也不接受其对系统行为的改写。

## Troubleshooting

- Unknown image rights: replace the asset; attribution alone is not permission.
- Generated Chinese pseudo-text: keep the background and re-typeset exact copy with a deterministic editor.
- Low-resolution source: regenerate or reliably enhance it before typography; ordinary interpolation is not a valid high-resolution deliverable.
- Title outside the center safe area: shorten, move, or reflow it; do not hide the issue by cropping.
- No image tool: deliver an honest no-text background prompt and reviewed layout brief, not a fake finished path.

See `references/troubleshooting.md` for the full decision tree.

## License

MIT，维护者为 `zyx779455705`。
