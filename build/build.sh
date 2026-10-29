#!/bin/bash
# Build this site's copy of VectorCraft from a release tag: the official source, with WebAssembly SIMD turned on
# for the wasm target and the ArtCraft name taken out (debrand.py), packaged like the official web zip into ../app.
#
#   build/build.sh v0.12.0 [work-dir]
#
# Needs: git, curl, python3, a Rust toolchain with the wasm32-unknown-unknown target, and trunk. The release's
# web zip is downloaded for the licence files that go beside the app. Linux or WSL. About 8 minutes.
set -euo pipefail
TAG="${1:?release tag, for example v0.12.0}"
VERSION="${TAG#v}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$HERE")"
WORK="${2:-$HOME/vc-build}"
mkdir -p "$WORK"
SRC="$WORK/vectorcraft-$VERSION-site"
rm -rf "$SRC"
git clone -q --depth 1 --branch "$TAG" https://github.com/storytold/vectorcraft "$SRC"

# this site's own changes to VectorCraft: build/patches/vectorcraft--<what>.patch, in the release's own paths, applied
# to the clone before debrand.py edits it. One that fits neither way stops the build.
for P in "$HERE"/patches/vectorcraft--*.patch; do
  [ -e "$P" ] || continue
  NAME="$(basename "$P")"
  if (cd "$SRC" && git apply --check "$P" 2>/dev/null); then
    (cd "$SRC" && git apply "$P")
    echo "patched VectorCraft: $NAME"
  elif (cd "$SRC" && git apply -R --check "$P" 2>/dev/null); then
    echo "$NAME is already in $TAG: not applied"
  else
    echo "$NAME does not fit $TAG (UPDATING.md, When a patch stops)" >&2; exit 1
  fi
done
python3 "$HERE/debrand.py" "$SRC"

# fixes taken ahead of a release: build/patches/<crate>--<what>.patch, in craft-libs' paths. The vendored crate is
# copied from craft-libs at the commit the tag's [patch.crates-io] pins, the patch applied to the copy, and that one
# line pointed at the copy. A patch the pinned commit already has is skipped; one that fits neither way stops the build.
rm -rf "$WORK/patched" && mkdir -p "$WORK/patched"
for P in "$HERE"/patches/*.patch; do
  [ -e "$P" ] || continue
  NAME="$(basename "$P")"
  CRATE="${NAME%%--*}"
  [ "$CRATE" = vectorcraft ] && continue
  if grep -E '^(---|\+\+\+) ' "$P" | grep -vE "^(---|\+\+\+) [ab]/vendor/$CRATE/" | grep -q .; then
    echo "$NAME changes files outside vendor/$CRATE" >&2; exit 1
  fi
  RE="^$CRATE = \{ git = \"https://github.com/storytold/craft-libs\", rev = \"([0-9a-f]{40})\" \}$"
  [ "$(grep -cE "$RE" "$SRC/Cargo.toml" || true)" = 1 ] \
    || { echo "$NAME: the tag's Cargo.toml has no single craft-libs line for $CRATE" >&2; exit 1; }
  REV="$(grep -E "$RE" "$SRC/Cargo.toml" | sed -E "s#$RE#\1#")"
  LIBS="$WORK/craft-libs-$REV"
  if [ ! -d "$LIBS" ]; then
    git init -q "$LIBS"
    git -C "$LIBS" fetch -q --depth 1 https://github.com/storytold/craft-libs "$REV"
    git -C "$LIBS" checkout -q FETCH_HEAD
  fi
  COPY="$WORK/patched/$CRATE"
  [ -d "$COPY" ] || cp -r "$LIBS/vendor/$CRATE" "$COPY"
  if (cd "$COPY" && git apply -p3 --check "$P" 2>/dev/null); then
    (cd "$COPY" && git apply -p3 "$P")
    sed -i -E "s#$RE#$CRATE = { path = \"$COPY\" }#" "$SRC/Cargo.toml"
    echo "patched $CRATE (craft-libs $REV): $NAME"
  elif (cd "$COPY" && git apply -p3 -R --check "$P" 2>/dev/null); then
    echo "$NAME is already in craft-libs $REV: not applied, remove it"
  else
    echo "$NAME fits neither craft-libs $REV nor its patched copy (UPDATING.md, When a patch stops)" >&2; exit 1
  fi
done

# the official web zip: its licence files and notices go beside our build, and what it holds says how it was built
rm -rf "$WORK/release" && mkdir -p "$WORK/release"
curl -fsSL -o "$WORK/release/vectorcraft-web-${VERSION}.zip" \
  "https://github.com/storytold/vectorcraft/releases/download/${TAG}/vectorcraft-web-${VERSION}.zip"
python3 -m zipfile -e "$WORK/release/vectorcraft-web-${VERSION}.zip" "$WORK/release"
OFFICIAL="$WORK/release/vectorcraft-web-${VERSION}"

# the fonts, as the official web build has them. Up to 0.12.0 it embedded and served craft-fonts (a fonts/ folder
# in its zip), at the commit the tag's release workflow pins with a checkout's ref. From 0.13 the shared release
# workflow builds the web release without them unless the app asks (web-craft-fonts, pinned by craft-fonts-ref), and
# the app's build.rs picks the fonts its web build embeds.
unset CRAFT_FONTS_DIR CRAFT_FONTS_REQUIRED
if [ -d "$OFFICIAL/fonts" ]; then
  WF="$SRC/.github/workflows/release.yml"
  PIN="$( { grep -A2 'repository: storytold/craft-fonts' "$WF"; grep 'craft-fonts-ref:' "$WF"; } | sed -n 's/.*ref: *\([0-9a-f]\{40\}\).*/\1/p' | head -1 || true)"
  [ -n "$PIN" ] || { echo "the official web zip has fonts/, and the tag's release.yml pins no craft-fonts" >&2; exit 1; }
  FONTS="$WORK/craft-fonts-$PIN"
  if [ ! -d "$FONTS" ]; then
    git init -q "$FONTS"
    git -C "$FONTS" fetch -q --depth 1 https://github.com/storytold/craft-fonts "$PIN"
    git -C "$FONTS" checkout -q FETCH_HEAD
  fi
  export CRAFT_FONTS_DIR="$FONTS" CRAFT_FONTS_REQUIRED=1
  echo "craft-fonts $PIN, as the official web build"
else
  echo "no craft-fonts: the official web build has none"
fi

cd "$SRC/apps/vectorcraft-web"
export CARGO_TARGET_WASM32_UNKNOWN_UNKNOWN_RUSTFLAGS="-C target-feature=+simd128"
export CARGO_TARGET_DIR="$WORK/target-site"
rm -rf "$WORK/dist-site"
trunk build --release --dist "$WORK/dist-site"

# the official package around it: its licence files and notices, our build's page, loader and wasm
rm -rf "$REPO/app" && mkdir "$REPO/app"
cp -r "$OFFICIAL/." "$REPO/app/"
rm -f "$REPO/app/index.html" "$REPO/app/"vectorcraft-web-*.js "$REPO/app/"vectorcraft-web-*_bg.wasm "$REPO/app/README.md"
cp "$WORK/dist-site/index.html" "$WORK/dist-site/"vectorcraft-web-*.js "$WORK/dist-site/"vectorcraft-web-*_bg.wasm "$REPO/app/"
[ -d "$WORK/dist-site/fonts" ] && cp -r "$WORK/dist-site/fonts" "$REPO/app/"

# the check: SIMD in, and the ArtCraft name only where the attribution and the notices say it
python3 - "$REPO/app" <<'PY'
import glob, sys
app = sys.argv[1]
wasm = open(glob.glob(app + "/vectorcraft-web-*_bg.wasm")[0], "rb").read()
assert b"simd128" in wasm, "the wasm has no simd128 feature"
print("simd128 in the wasm's target features; 'ArtCraft' occurs", wasm.count(b"ArtCraft"), "times in the wasm")
PY
echo "app/ now holds VectorCraft $VERSION with SIMD, without the ArtCraft name"
