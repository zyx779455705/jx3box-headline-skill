# JX3BOX Headline Skill

为剑网3魔盒 JX3BOX 文章制作、修改和审查 `3200×560`、`1600×280`、`600×200` 或带显式安全区的自定义头条图。技能覆盖标题压缩、字体与图片授权、三类图文构图、精确中文排版和交付 QA。

## Installation

### Windows PowerShell

克隆仓库并运行安全安装器（默认安装到通用技能目录）：

```powershell
git clone https://github.com/zyx779455705/jx3box-headline-skill.git
Set-Location .\jx3box-headline-skill
.\install.ps1 -DryRun
.\install.ps1
```

### macOS / Linux

```sh
git clone https://github.com/zyx779455705/jx3box-headline-skill.git
cd jx3box-headline-skill
sh install.sh --dry-run
sh install.sh
```

安装器默认不会覆盖已有目录。确认目标后才使用 `-Force`（PowerShell）或 `--force`（POSIX）；也可用 `-Platform`/`--platform`、`-Project`/`--project` 或 `-Path`/`--path` 指定宿主和位置。

### Manual paths

| Platform | Native path |
|---|---|
| Codex CLI / universal | `~/.agents/skills/jx3box-headline-skill/` |
| Claude Code | `~/.claude/skills/jx3box-headline-skill/` |
| GitHub Copilot | `~/.copilot/skills/jx3box-headline-skill/` |
| Gemini CLI | `~/.gemini/skills/jx3box-headline-skill/` |
| Cursor（项目级） | `.cursor/skills/jx3box-headline-skill/` |

仓库根目录中的 `install.sh` 与 `install.ps1` 是安装器；`jx3box-headline-skill` 与 `jx3box-headline-skill.ps1` 只是可选简报校验器的启动脚本。

更新源码仓库：

```powershell
git pull
.\install.ps1 -DryRun
.\install.ps1 -Force
```

## Prerequisites

- Agent host with SKILL.md support.
- Host image generation/editing tool for final bitmap work.
- Python 3.10+ is optional and used only for the bundled deterministic brief validator/evals; no third-party package, API key, or runtime network access is required.
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
/jx3box-headline-skill 把这篇文章做成600x200头条，中心文字不要被裁切
/jx3box-headline-skill 这张插画来源不确定，判断能不能用于魔盒文章封面
/jx3box-headline-skill 只生成无字背景，并给出精确中文排版坐标
```

## Deterministic brief validation

Prepare JSON using `references/workflow-guide.md`, then run:

```powershell
.\jx3box-headline-skill.ps1 --input brief.json --output validated-brief.json
```

`ready_for_render: false` means blocked assets or font rights must be resolved before final image work. A successful process exit only confirms the JSON and structural rules are valid.

`resolution` 可使用 `high`、`standard`、`compact`；其他尺寸必须提供完整的 `safe_area`。素材最好提供唯一 `id`。署名通过 `attribution_required` 和 `attribution_placement` 区分画内、元数据与 README，不再把所有第三方字体署名都画进头条。

## Verification

Run unit tests:

```powershell
python -m unittest discover -s tests -v
```

Validate the bundled eval spec:

```powershell
python scripts\run_evals.py --validate
python scripts\run_evals.py --rollout
```

评测会执行 3 个确定性黄金用例，并检查 JSON、画布/安全区和保守授权规则。语义标题、构图质量和最终中文可读性仍由人工或 LLM 复核，不能由简报校验器替代。

CI 在 Windows 与 Linux、Python 3.10 与 3.13 上运行编译、18 项单元测试、评测规范、完整 rollout、JSON 资源和安装器检查。

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
- Title outside the center safe area: shorten, move, or reflow it; do not hide the issue by cropping.
- No image tool: deliver an honest no-text background prompt and validated layout brief, not a fake finished path.

See `references/troubleshooting.md` for the full decision tree.

## License

MIT，维护者为 `zyx779455705`。初版由 OpenAI Codex 协助生成。第三方字体和图片保留各自许可，必须分别核验。
