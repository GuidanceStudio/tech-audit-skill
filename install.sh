#!/usr/bin/env bash
set -euo pipefail

# code-audit skill installer.
#
# Copies the skill files into the user's Claude skill directory so the
# `/code-audit` slash command and routing become available.
#
# Local mode:  ./install.sh [OPTIONS]
# Remote mode: bash <(curl -fsSL https://raw.githubusercontent.com/GuidanceStudio/code-repository-audit-skill/main/install.sh)

REPO_URL="${CODE_AUDIT_REPO_URL:-https://github.com/GuidanceStudio/code-repository-audit-skill.git}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FORCE=false
TARGET_DIR="${HOME}/.claude/skills/code-audit"
CLEANUP_DIR=""

cleanup_temp() {
    if [ -n "$CLEANUP_DIR" ] && [ -d "$CLEANUP_DIR" ]; then
        rm -rf "$CLEANUP_DIR"
    fi
}
trap cleanup_temp EXIT

usage() {
    cat <<EOF
Install the code-audit Claude skill.

Usage:
    ./install.sh [OPTIONS]

Options:
    --force         Overwrite an existing installation without prompting.
    --check         Compare the installed copy against the source tree
                    (no writes); exits 1 and reports DRIFT on differences.
    --target DIR    Install to DIR instead of $TARGET_DIR.
    --help          Show this message.

Environment:
    CODE_AUDIT_REPO_URL     Override the remote-mode clone URL.
EOF
}

CHECK=false
while [ $# -gt 0 ]; do
    case "$1" in
        --force) FORCE=true; shift ;;
        --check) CHECK=true; shift ;;
        --target) TARGET_DIR="$2"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) echo "unknown option: $1" >&2; usage; exit 1 ;;
    esac
done

# Detect local vs remote mode
if [ -d "$SCRIPT_DIR/claude/code-audit" ]; then
    SRC_ROOT="$SCRIPT_DIR/claude/code-audit"
else
    if ! command -v git >/dev/null 2>&1; then
        echo "error: remote install requires 'git' on PATH" >&2
        exit 1
    fi
    CLEANUP_DIR="$(mktemp -d)"
    echo "Cloning $REPO_URL into temporary dir..."
    git clone --depth=1 "$REPO_URL" "$CLEANUP_DIR" >/dev/null 2>&1
    SRC_ROOT="$CLEANUP_DIR/claude/code-audit"
    if [ ! -d "$SRC_ROOT" ]; then
        echo "error: cloned repo does not contain claude/code-audit/" >&2
        exit 1
    fi
fi

# Drift check mode — no writes
if [ "$CHECK" = true ]; then
    if [ ! -d "$TARGET_DIR" ]; then
        echo "DRIFT: code-audit is not installed at $TARGET_DIR"
        exit 1
    fi
    DIFF_OUT="$(diff -r --exclude=__pycache__ --exclude=.installed-from "$SRC_ROOT" "$TARGET_DIR" 2>&1)" || true
    if [ -n "$DIFF_OUT" ]; then
        echo "DRIFT: $TARGET_DIR differs from the source tree:"
        echo "$DIFF_OUT" | head -10
        exit 1
    fi
    echo "OK: $TARGET_DIR matches the source tree"
    exit 0
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
find "$TARGET_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Stamp the source git SHA so "what version is deployed?" has an answer
if git -C "$(dirname "$SRC_ROOT")" rev-parse --short HEAD >/dev/null 2>&1; then
    git -C "$(dirname "$SRC_ROOT")" rev-parse --short HEAD > "$TARGET_DIR/.installed-from"
fi

echo
echo "✅ Installed code-audit skill to $TARGET_DIR"
echo
echo "Invoke from Claude with /code-audit, or by asking for an audit:"
echo "    \"audit my codebase\""
echo "    \"security review\""
echo "    \"is this ready to ship?\""
