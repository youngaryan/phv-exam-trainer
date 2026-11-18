#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
target="$PWD/app/index.html"
if [ "$(uname -s)" = "Darwin" ]; then
  open "$target"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$target"
else
  printf 'Open this file in a browser: %s\n' "$target"
fi
