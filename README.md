# JX3BOX Headline Skill

为剑网3魔盒 JX3BOX 文章制作、修改和审查 `3200×560` 或 `1600×280` 头条图。技能覆盖标题压缩、字体与图片授权、中心安全区、三类图文构图、精确中文排版和交付 QA。

## Installation

### Windows PowerShell

克隆到通用技能目录：

```powershell
git clone https://github.com/zyx779455705/jx3box-headline-skill.git "$env:USERPROFILE\.agents\skills\jx3box-headline-skill"
```

### macOS / Linux

```sh
git clone https://github.com/zyx779455705/jx3box-headline-skill.git ~/.agents/skills/jx3box-headline-skill
chmod +x ~/.agents/skills/jx3box-headline-skill/jx3box-headline-skill
```

### Manual paths

| Platform | Native path |
|---|---|
| Codex CLI / universal | `~/.agents/skills/jx3box-headline-skill/` |
| Claude Code | `~/.claude/skills/jx3box-headline-skill/` |
| GitHub Copilot | `~/.copilot/skills/jx3box-headline-skill/` |
| Gemini CLI | `~/.gemini/skills/jx3box-headline-skill/` |
| Cursor | `.cursor/skills/jx3box-headline-skill/` |

也可以把仓库克隆到上表对应宿主的原生技能目录。仓库根目录中的
`jx3box-headline-skill` 与 `jx3box-headline-skill.ps1` 是简报校验器启动脚本，
不是安装器。

## Prerequisites

- Agent host with SKILL.md support.
- Host image generation/editing tool for final bitmap work.
- Python 3.10+ only for the bundled brief validator; no third-party package, API key, or runtime network access is required.
- Verified rights for every supplied image, illustration, texture, and font.

Check the validator runtime:

```powershell
.\jx3box-headline-skill.ps1 --check-prereqs
```

## Usage

Open a new agent session and invoke:

```text
/jx3box-headline-skill 给我的明尊T入门攻略做一张3200x560魔盒头条
```

Other examples:

```text
/jx3box-headline-skill 用我附上的游戏截图做“衍天试炼”封面，人物和标题做穿插
/jx3box-headline-skill 把“从入门到进阶手把手教你的超级明尊T攻略”改成适合头条的主副标题
/jx3box-headline-skill 检查这张头条在1600x280下的安全区和小字可读性
/jx3box-headline-skill 这张插画来源不确定，判断能不能用于魔盒文章封面
/jx3box-headline-skill 只生成无字背景，并给出精确中文排版坐标
```

## Deterministic brief validation

Prepare JSON using `references/workflow-guide.md`, then run:

```powershell
.\jx3box-headline-skill.ps1 --input brief.json --output validated-brief.json
```

`ready_for_render: false` means blocked assets or font rights must be resolved before final image work. A successful process exit only confirms the JSON and structural rules are valid.

## Verification

Run unit tests:

```powershell
python -m unittest discover -s tests -v
```

Validate the bundled eval spec:

```powershell
python scripts\run_evals.py --validate
```

The creative bitmap workflow intentionally has no deterministic rollout command. Golden cases remain pending until a user approves the first accepted output.

## Source material

The local rules are derived from three JX3BOX tutorials:

- [文字篇](https://www.jx3box.com/community/609)
- [图片篇](https://www.jx3box.com/community/607)
- [技巧篇](https://www.jx3box.com/community/608)

The skill is self-contained at runtime. Review those pages when the dependency staleness interval expires or JX3BOX changes its cover behavior.

## Troubleshooting

- Unknown image rights: replace the asset; attribution alone is not permission.
- Generated Chinese pseudo-text: keep the background and re-typeset exact copy with a deterministic editor.
- Title outside the center safe area: shorten, move, or reflow it; do not hide the issue by cropping.
- No image tool: deliver an honest no-text background prompt and validated layout brief, not a fake finished path.

See `references/troubleshooting.md` for the full decision tree.

## License

MIT. Third-party fonts and images retain their own licenses and must be verified separately.
