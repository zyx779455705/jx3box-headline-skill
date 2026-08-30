#!/bin/sh
# Template-derived, conservative installer for jx3box-headline-skill.
set -eu

SKILL_NAME="jx3box-headline-skill"
VERSION="1.1.0"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PLATFORM="universal"
PROJECT=false
CUSTOM_PATH=""
DRY_RUN=false
FORCE=false

show_help() {
    printf '%s\n' "Install ${SKILL_NAME} ${VERSION}"
    printf '%s\n' "Usage: ./install.sh [--platform NAME] [--project] [--path EXACT_DESTINATION] [--dry-run] [--force]"
    printf '%s\n' "Platforms: universal, codex, claude-code, copilot, gemini, cursor"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --platform) [ "$#" -ge 2 ] || { printf '%s\n' "Missing --platform value" >&2; exit 1; }; PLATFORM=$2; shift 2 ;;
        --project) PROJECT=true; shift ;;
        --path) [ "$#" -ge 2 ] || { printf '%s\n' "Missing --path value" >&2; exit 1; }; CUSTOM_PATH=$2; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --force) FORCE=true; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) printf '%s\n' "Unknown option: $1" >&2; show_help; exit 1 ;;
    esac
done

case "$PLATFORM" in
    universal|codex|claude-code|copilot|gemini|cursor) ;;
    *) printf '%s\n' "Unsupported platform: $PLATFORM" >&2; exit 2 ;;
esac

[ -f "$SCRIPT_DIR/SKILL.md" ] || { printf '%s\n' "SKILL.md is missing from $SCRIPT_DIR" >&2; exit 1; }

if [ -n "$CUSTOM_PATH" ]; then
    INSTALL_DIR=$CUSTOM_PATH
elif $PROJECT; then
    case "$PLATFORM" in
        claude-code) BASE=".claude/skills" ;;
        copilot) BASE=".github/skills" ;;
        gemini) BASE=".gemini/skills" ;;
        cursor) BASE=".cursor/skills" ;;
        *) BASE=".agents/skills" ;;
    esac
    INSTALL_DIR="$(pwd)/${BASE}/${SKILL_NAME}"
else
    case "$PLATFORM" in
        claude-code) BASE="${HOME}/.claude/skills" ;;
        copilot) BASE="${HOME}/.copilot/skills" ;;
        gemini) BASE="${HOME}/.gemini/skills" ;;
        cursor) printf '%s\n' "Cursor requires --project or --path" >&2; exit 2 ;;
        *) BASE="${HOME}/.agents/skills" ;;
    esac
    INSTALL_DIR="${BASE}/${SKILL_NAME}"
fi

case "$INSTALL_DIR" in
    /*) ;;
    *) INSTALL_DIR="$(pwd)/$INSTALL_DIR" ;;
esac

case "$INSTALL_DIR" in
    ""|/|"$HOME") printf '%s\n' "Refusing unsafe destination: $INSTALL_DIR" >&2; exit 3 ;;
    */"$SKILL_NAME") ;;
    *) printf '%s\n' "Destination must end with ${SKILL_NAME}: $INSTALL_DIR" >&2; exit 3 ;;
esac

if [ "$SCRIPT_DIR" = "$INSTALL_DIR" ]; then
    printf '%s\n' "Already installed at $INSTALL_DIR"
    exit 0
fi

if $DRY_RUN; then
    printf '%s\n' "[dry-run] $SCRIPT_DIR -> $INSTALL_DIR"
    exit 0
fi

if [ -e "$INSTALL_DIR" ]; then
    if ! $FORCE; then
        printf '%s\n' "Destination exists; use --force to replace only: $INSTALL_DIR" >&2
        exit 3
    fi
    rm -rf -- "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
for item in "$SCRIPT_DIR"/* "$SCRIPT_DIR"/.[!.]* "$SCRIPT_DIR"/..?*; do
    [ -e "$item" ] || continue
    name=$(basename "$item")
    case "$name" in .git|__pycache__|.pytest_cache) continue ;; esac
    case "$INSTALL_DIR/" in "$item"/*) continue ;; esac
    cp -R "$item" "$INSTALL_DIR/"
done

printf '%s\n' "Installed ${SKILL_NAME} ${VERSION} to ${INSTALL_DIR}"
printf '%s\n' "Open a new agent session and invoke /${SKILL_NAME}"
