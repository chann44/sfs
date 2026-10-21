#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${SFS_INSTALL_DIR:-$HOME/.local/share/sfs}"
BIN_DIR="${SFS_BIN_DIR:-$HOME/.local/bin}"
BIN="$BIN_DIR/sfs"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

say() { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$1" >&2; exit 1; }

uninstall() {
	say "removing $INSTALL_DIR"
	rm -rf "$INSTALL_DIR"
	say "removing $BIN"
	rm -f "$BIN"
	say "uninstalled"
	exit 0
}

[[ "${1:-}" == "--uninstall" || "${1:-}" == "-u" ]] && uninstall

[[ -f "$SRC_DIR/main.py" ]] || die "run this from the sfs repo (main.py not found next to install.sh)"

command -v python3 >/dev/null 2>&1 || die "python3 not found"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' \
	|| die "python3 >= 3.12 required (found $(python3 --version))"

say "installing to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
rm -rf "$INSTALL_DIR/core" "$INSTALL_DIR/cli" "$INSTALL_DIR/tools"
cp -R "$SRC_DIR/core" "$SRC_DIR/cli" "$SRC_DIR/tools" "$INSTALL_DIR/"
cp "$SRC_DIR/main.py" "$INSTALL_DIR/main.py"
find "$INSTALL_DIR" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

say "creating $BIN"
mkdir -p "$BIN_DIR"
printf '#!/bin/sh\nexec python3 "%s/main.py" "$@"\n' "$INSTALL_DIR" > "$BIN"
chmod +x "$BIN"

case ":$PATH:" in
	*":$BIN_DIR:"*) ;;
	*)
		printf '\n\033[1;33mwarning:\033[0m %s is not on your PATH\n' "$BIN_DIR"
		printf 'add it with:\n\n    echo '\''export PATH="%s:$PATH"'\'' >> ~/.%src && source ~/.%src\n\n' \
			"$BIN_DIR" "${SHELL##*/}" "${SHELL##*/}"
		;;
esac

say "done"
"$BIN" --help >/dev/null 2>&1 || die "install verification failed"
printf 'try it:  sfs init you\n         sfs shell\n         sfs --mcp\n'
