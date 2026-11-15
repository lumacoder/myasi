#!/usr/bin/env sh
# One-line install: curl -fsSL https://raw.githubusercontent.com/lumacoder/myasi/main/scripts/install.sh | sh
# Downloads only myasi.py + wrapper into ~/.myasi/bin (no full clone). Private repo: export GITHUB_TOKEN first.
# MYASI_RAW_URL overrides the download base (a mirror, or a local server for tests).
set -e
REPO="${MYASI_REPO:-lumacoder/myasi}"; REF="${MYASI_REF:-main}"
BIN="${MYASI_HOME:-$HOME/.myasi}/bin"
mkdir -p "$BIN"
URL="${MYASI_RAW_URL:-https://raw.githubusercontent.com/$REPO/$REF}"
TOK="${GITHUB_TOKEN:-$GH_TOKEN}"
if [ -n "$TOK" ] && [ -z "$MYASI_RAW_URL" ]; then
  URL="https://api.github.com/repos/$REPO/contents"
  for f in scripts/myasi.py bin/myasi; do
    curl -fsSL -H "Authorization: Bearer $TOK" -H "Accept: application/vnd.github.raw" "$URL/$f?ref=$REF" -o "$BIN/$(basename "$f")"
  done
else
  curl -fsSL "$URL/scripts/myasi.py" -o "$BIN/myasi.py"
  curl -fsSL "$URL/bin/myasi" -o "$BIN/myasi"
fi
chmod +x "$BIN/myasi"
echo "installed: $BIN/myasi"
case ":$PATH:" in *":$BIN:"*) ;; *) echo "add to PATH:  export PATH=\"$BIN:\$PATH\"";; esac
"$BIN/myasi" --version
