#!/bin/bash
# A built copy of a JupyterLab commit that needs no install of its own: the takes of `main` serve it.
# Usage: build_main.sh <ref> [destination]
# JUPYTERLAB_SRC is a JupyterLab checkout with its node_modules installed (jlpm install). The copy links to those
# node_modules, compiles the TypeScript and bundles the app, and leaves the checkout as it was.
set -euo pipefail
R="${JUPYTERLAB_SRC:?set JUPYTERLAB_SRC to a JupyterLab checkout with node_modules}"
REF=${1:?ref}
C=${2:-${RV_BASE:-${RV_WORK:-$(cd "$(dirname "$0")/.." && pwd)/work}/runtime}/main}
mkdir -p "$(dirname "$C")"
mkdir "$C"
git -C "$R" archive "$REF" | tar -xm -C "$C"
mkdir "$C/node_modules"
for e in "$R"/node_modules/* "$R"/node_modules/.bin; do
  n=$(basename "$e")
  case "$n" in
    @jupyterlab|@types|@jupyter) mkdir "$C/node_modules/$n" ;;
    *) ln -s "$e" "$C/node_modules/$n" ;;
  esac
done
# The workspace packages point into the copy, everything else into the checkout.
for e in "$R"/node_modules/@jupyterlab/*; do
  n=$(basename "$e")
  if [ -L "$e" ] && [[ "$(readlink "$e")" == ../* ]]; then cp -P "$e" "$C/node_modules/@jupyterlab/$n"; else ln -s "$e" "$C/node_modules/@jupyterlab/$n"; fi
done
for e in "$R"/node_modules/@types/*; do ln -s "$e" "$C/node_modules/@types/$(basename "$e")"; done
for e in "$R"/node_modules/@jupyter/*; do
  n=$(basename "$e")
  if [ "$n" = builder ]; then cp -r "$e" "$C/node_modules/@jupyter/$n"; else ln -s "$e" "$C/node_modules/@jupyter/$n"; fi
done
cp -r "$R/dev_mode/node_modules" "$C/dev_mode/node_modules"
cd "$C"
time node_modules/.bin/tsc -b packages/metapackage
(cd "$C/dev_mode" && time node ../node_modules/.bin/rspack --config webpack.config.js > "$C/rspack.log" 2>&1)
# Schemas come from the checkout through the builder: copy the copy's own.
for d in packages/*/schema; do
  pkg=$(node -e "console.log(require('./$(dirname $d)/package.json').name)")
  if [ -d "dev_mode/schemas/$pkg" ]; then cp "$d"/*.json "dev_mode/schemas/$pkg/"; fi
done
echo BUILD-OK "$(git -C "$R" rev-parse --short "$REF")"
