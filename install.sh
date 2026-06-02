#!/usr/bin/env bash
set -euo pipefail

# code-review skill installer.
#
# Copies the skill files into the user's Claude skill directory so the
# `/code-review` slash command and routing become available.
#
# Local mode:  ./install.sh [OPTIONS]
# Remote mode: bash <(curl -fsSL https://raw.githubusercontent.com/GuidanceStudio/code-repository-audit-skill/main/install.sh)

REPO_URL="${CODE_REVIEW_REPO_URL:-https://github.com/GuidanceStudio/code-repository-audit-skill.git}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FORCE=false
TARGET_DIR="${HOME}/.claude/skills/code-review"
CLEANUP_DIR=""

cleanup_temp() {
    if [ -n "$CLEANUP_DIR" ] && [ -d "$CLEANUP_DIR" ]; then
        rm -rf "$CLEANUP_DIR"
    fi
}
trap cleanup_temp EXIT

usage() {
    cat <<EOF
Install the code-review Claude skill.

Usage:
    ./install.sh [OPTIONS]

Options:
    --force         Overwrite an existing installation without prompting.
    --target DIR    Install to DIR instead of $TARGET_DIR.
    --help          Show this message.

Environment:
    CODE_REVIEW_REPO_URL    Override the remote-mode clone URL.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --force) FORCE=true; shift ;;
        --target) TARGET_DIR="$2"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) echo "unknown option: $1" >&2; usage; exit 1 ;;
    esac
done

# Detect local vs remote mode
if [ -d "$SCRIPT_DIR/claude/code-review" ]; then
    SRC_ROOT="$SCRIPT_DIR/claude/code-review"
else
    if ! command -v git >/dev/null 2>&1; then
        echo "error: remote install requires 'git' on PATH" >&2
        exit 1
    fi
    CLEANUP_DIR="$(mktemp -d)"
    echo "Cloning $REPO_URL into temporary dir..."
    git clone --depth=1 "$REPO_URL" "$CLEANUP_DIR" >/dev/null 2>&1
    SRC_ROOT="$CLEANUP_DIR/claude/code-review"
    if [ ! -d "$SRC_ROOT" ]; then
        echo "error: cloned repo does not contain claude/code-review/" >&2
        exit 1
    fi
fi

# Confirm overwrite
if [ -d "$TARGET_DIR" ]; then
    if [ "$FORCE" = true ]; then
        rm -rf "$TARGET_DIR"
    else
        printf "Target %s already exists. Overwrite? [y/N] " "$TARGET_DIR"
        read -r ans
        case "$ans" in
            y|Y|yes) rm -rf "$TARGET_DIR" ;;
            *) echo "Aborted."; exit 1 ;;
        esac
    fi
fi

mkdir -p "$(dirname "$TARGET_DIR")"
cp -r "$SRC_ROOT" "$TARGET_DIR"

echo
echo "✅ Installed code-review skill to $TARGET_DIR"
echo
echo "Invoke from Claude with /code-review, or by asking for a review:"
echo "    \"review this PR\""
echo "    \"audit my codebase\""
echo "    \"security review\""
echo "    \"is this ready to ship?\""
