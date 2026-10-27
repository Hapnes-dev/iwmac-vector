# Updating VectorCraft on this site

This is the runbook for moving https://hapnes-dev.github.io/iwmac-vector/app/ to a new VectorCraft release. The
build is made from the release's official source with two changes: WebAssembly SIMD, and no ArtCraft name. The
[README](README.md) says why.

The whole update takes about an hour, most of it waiting for builds.

## At a glance

| Step | What | Where |
|---|---|---|
| 1 | Read the release notes | `gh release view vX.Y.Z -R storytold/vectorcraft` |
| 2 | Build it to try, without committing | Actions › *Update VectorCraft*, *commit* unticked |
| 3 | Check the build | `python3 build/check.py <folder>` (the workflow runs it too) |
| 4 | Look at it and time it | a local server, and `build/bench-drawing.py` |
| 5 | Test the userscript on it | before going live if you can, otherwise right after (see step 5) |
| 6 | Publish | Actions › *Update VectorCraft*, *commit* ticked |
| 7 | Check the live site | `python3 build/check.py https://hapnes-dev.github.io/iwmac-vector/app/` |
| 8 | Update the notes | the userscript's README, and the kit's change log |

If anything goes wrong after publishing, [roll back](#rolling-back).

## 1. Read the release notes

```bash
gh release list -R storytold/vectorcraft --limit 5
gh release view v0.12.0 -R storytold/vectorcraft
```

Look for changes to what the userscript relies on:
- the **Save As** dialog and its SVG Options;
- opening a **dropped file**;
- saving through a **download**;
- the **title** (a `*` marks unsaved changes);
- the canvas element `#vectorcraft_canvas`.

Look also for changes to the parts `build/debrand.py` edits: the Help menu, the About box, the Discord button and
the community links.

And look whether each fix in `build/patches/` is in the release yet: the head of each patch says where it comes
from. `build.sh` says so too, and a patch that is in can go (see
[Fixes taken ahead of a release](#fixes-taken-ahead-of-a-release)).

## 2. Build it to try

**On GitHub.** Go to Actions › *Update VectorCraft* › *Run workflow*. Enter the tag, untick **commit**, and run. It
takes about 15 to 25 minutes. The result is an artifact, `app-vX.Y.Z`; download it from the run's page. Nothing in
the repository changes.

**Or locally**, in Linux or WSL. It takes about 8 minutes once the toolchain is installed (see the
[local build setup](#local-build-setup)).

```bash
build/build.sh v0.12.0 ~/vc-build
```

This writes `app/` in your working copy. Look before you commit: `git diff --stat`.

**If the build stops in `debrand.py`**, see [When debrand.py stops](#when-debrandpy-stops).

## 3. Check the build

```bash
python3 build/check.py path/to/app-vX.Y.Z
```

Every line must read PASS. The workflow runs the same check and fails if any line fails. It checks:

| Check | Why |
|---|---|
| The page's SHA-384 (integrity) matches the loader and the wasm | A changed file, a line ending included, stops the editor from loading |
| `simd128` is in the wasm's target features | The whole point of this build: about 2.3 times as fast |
| "ArtCraft" appears exactly once, in "Based on VectorCraft by the ArtCraft team" | The brand terms: a modified build carries no ArtCraft marks |
| No ArtCraft links (getartcraft.com, discord.gg/artcraft) | The same |
| The version string | That it is the release you meant |
| The embedded UI font (BIZ UDPGothic) | Only a warning: craft-fonts' web set can change, and from 0.13 the official web build embeds none |
| `LICENSE-MIT` and `LICENSE-APACHE` present, VectorCraft's own `README.md` left out | Licences go with it; their README carries the brand |

## 4. Look at it and time it

Serve the folder, open it, and look at three things:

```bash
cd path/to/app-vX.Y.Z && python3 -m http.server 8780
```

- **The start page.** There is no Discord button in the bar, and under *Community* only *Source code on GitHub*.
- **Help.** It lists *VectorCraft on GitHub*, *Search Commands…*, *VectorCraft Help…* and *About VectorCraft*, with
  no ArtCraft entries.
- **Help › About.** It shows the new version and the line *Based on VectorCraft by the ArtCraft team, built with
  WebAssembly SIMD …*

**Timing.** Make the test drawing, and time it in the build you are trying and in the live editor, in the same
window size:

```bash
python3 build/bench-drawing.py > bench.svg
```

1. Drop `bench.svg` on the canvas.
2. Click the small red square at the bottom right, and drag it around.
3. Read `render N ms` at the right end of the status bar.

On 2026-10-17, at 1400 x 900, VectorCraft 0.11.0 drew 13.7 ms a frame as the official build and 5.3 ms as this
build. The new build should be about as fast as the live one, or faster.

## 5. Test the userscript on it

The userscript (IWMAC Designer Import/Export) runs on this page and drives VectorCraft from outside: it drops files,
answers Save As, and catches the saved SVG. A VectorCraft release can break that without breaking anything else.

**Before going live**, with Claude's local test bed: the stub Designer, and the e2e cases with the 10214 panels.
These live outside this public repository. The kit repository (private) explains them in
`iwmac-designer-import-export/VECTORCRAFT-UPDATE.md`. They serve the build you are trying at this site's address,
then compare it with the live build:
- syncs that must place as many objects as on the live build;
- the .ai flow;
- the first save, which must answer Save As by the clicks alone (the userscript answers by clicks first since
  1.83.2).

**By hand, right after going live** (5 minutes, in the live Designer, on a test panel):
1. Open the panel in the IWMAC Designer and choose **Edit in VectorCraft**. The drawing and its objects open, and
   the card says *Ready to sync* after a few seconds. No Save As dialog stays on screen.
2. Move one object and press **Ctrl+S**. The Designer's tab shows *✓ Synced*, and the object has moved on the
   panel.
3. Press Ctrl+Z in VectorCraft and Ctrl+S again, so the panel is as it was.

If step 1 takes much longer than before, or a Save As dialog flashes, the userscript's Save As keys no longer
fit. The userscript then falls back to clicks, which still works, but slower. See the userscript's README, *The
hosted copy*, which says what each version needs.

### Known: VectorCraft 0.12.0's Save As

In 0.12.0 the format list stays open after a key picks SVG:
- Space and Enter select an item, and the list stays open;
- Tab moves within the list;
- Escape closes the whole dialog.

So the userscript's keys can no longer reach OK. Its click fallback (*Format ▾*, *SVG*, *OK*, at the same places
as in 0.11.0) still works. Measured against 0.11.0, the first save was ready after 16.5 s instead of 10.8 s, and
an .ai's sync took 8.2 s instead of 2.4 s.

Change the userscript before moving to 0.12.0: in `answerSaveAs`, use the clicks first, or click OK once the keys
have taken SVG. The userscript does the clicks first since 1.83.2.

### Known: VectorCraft 0.13.1, built and not published

Tried on 2026-10-18. The build and `check.py` passed, and so did the userscript's syncs and its first save by the
clicks (in 0.13.1 the keys take *VectorCraft Template*). It stayed unpublished for what it makes of an `.ai`:
- A stroked zigzag in our test drawings opens as its bounding rectangle. The official 0.13.1 build does the same, byte
  for byte, so it is the release, not this build.
- The colours taken from an `.ai` move by up to 8 in a channel.

Before the next release, open the same `.ai` files in it and in the live build, save both as SVG, and compare the
paths.

### Known: VectorCraft 0.14.0, published with one fix taken ahead

Built, tested and published on 2026-10-22.
- **The heat exchanger.** The release still opens the stroked zigzag as its bounding rectangle, as 0.12.0 and 0.13.1
  did, and so does its official build. The fix is upstream in craft-libs, not merged yet, so this build takes it
  from `build/patches/` (see [Fixes taken ahead of a release](#fixes-taken-ahead-of-a-release)). With it, every shape
  of the test `.ai` files (2349's, 3530's and 2313's Maskin, 2313's VGV, the Maskin template) opens as in 0.11.0.
- **Colours from an `.ai`** still move by up to 8 in a channel, as in 0.13.1: from 0.12 VectorCraft converts CMYK
  through colour management. Illustrator's own export of the same drawing is a little nearer 0.11.0's colours. Shown
  here, not changed.
- **Fonts.** The official web zip carries craft-fonts again (with Noto Sans Georgian), so this build does too, at the
  commit the release workflow names.
- **The userscript (1.100.0):** its syncs placed as many objects as on 0.11.0, the `.ai` flow gave the same results,
  and the first save was answered by the clicks alone, ready after 11.5 s (11.9 s on 0.11.0). A component dragged
  onto the drawing lands about 2 px from where 0.11.0 put it.
- **Speed:** a drag frame on 10214's Maskin at 1400 x 900 drew in 5.9 to 8.1 ms, against 5.3 to 8.9 ms in 0.11.0 and
  14.8 to 19.3 ms in the official 0.14.0 build.

### Known: VectorCraft 0.17.0, published with the same fix

Built, tested and published on 2026-10-27. 0.15.0 and 0.16.0 were never hosted.
- **The heat exchanger.** 0.15.0 to 0.17.0 still open the zigzag as a rectangle, and so does the official 0.17.0
  build. The upstream pull request with the fix was closed unmerged on 2026-10-24, when a batch of PDF reader fixes
  was merged that leaves this one to it, so craft-libs' `main` still lacks it. 0.17.0 pins a newer craft-libs commit
  (`2eca9b3`), and the patch applied to it unchanged. With it, every shape of the test `.ai` files opens as in 0.14.0.
- **One label reads differently.** The Maskin template's "To offset", which the `.ai` keeps as the text "To o",
  the outlined letters "ff" and the text "set", opens as one text "To offset". Its synced picture draws it about
  3 px longer.
- **The userscript (1.104.1):** its syncs placed as many objects as on 0.14.0 (77, 107, 77), the `.ai` flow gave
  the same results apart from that label, and the first save was answered by the clicks alone, ready after 10.9 s
  as on 0.14.0.
- **Colours** from an `.ai` are the same as in 0.14.0.
- **Drawing.** Since 0.15 a pan, zoom or drag moves the last frame, and renders once the view is still. While
  dragging, the status bar's *render* reads about 0 ms at 240 fps, so `bench-drawing.py`'s readout no longer shows
  what SIMD saves. Measured instead as the longest frame after a zoom step on 10214's Maskin at 1400 x 900 (median
  of ten): 8.4 ms in this build, 12.4 ms in 0.14.0, 16.7 ms in the official 0.17.0.
- **The wasm is 76.7 MB**, up from 73.1 MB in 0.14.0. GitHub refuses a file over 100 MB, so a later release may need
  the wasm split or served from elsewhere.
- **Watch for:** upstream has asked to name an opened SVG or PDF from its own title metadata, or its file stem,
  instead of its file name. A first attempt was closed unmerged on 2026-10-25. The userscript waits for the window
  title to be the file's name, so test that flow closely in the release that brings it.

## 6. Publish

Actions › *Update VectorCraft* › *Run workflow*, with the tag and **commit** ticked. The workflow builds again,
runs `check.py`, then:
- replaces `app/`;
- sets the version in `index.html` and in the README's *Currently* line;
- commits *VectorCraft vX.Y.Z: built from the official source with WebAssembly SIMD, without the ArtCraft name*.

Pages publishes about a minute later.

**Or locally**, after `build/build.sh`:
1. Edit the version in `index.html` (*VectorCraft X.Y.Z, an open-source…*) and in the README's *Currently* line.
2. Commit `app/`, `index.html` and `README.md`, then push.

## 7. Check the live site

```bash
python3 build/check.py https://hapnes-dev.github.io/iwmac-vector/app/
```

Then reload the editor with Ctrl+F5 and look at Help › About for the version. Pages caches for about 10 minutes.

## 8. Update the notes

- The userscript's README (Hapnes-dev/tampermonkey-scripts), *Edit in VectorCraft › The hosted copy*: the version,
  the date, and anything the release changed for the userscript.
- The kit's `documentation-change-log.md`: a Part for the update.

## Rolling back

```bash
git revert <the update's commit>
git push
```

Pages serves the previous build a minute later. The editor keeps documents per browser, so they survive a
rollback, unless the new version changed its file format. Read the release notes for that.

## Fixes taken ahead of a release

When a release breaks something the userscript's drawings need, and a fix exists upstream but is not released, the
fix can go in `build/patches/` until a release has it. Since 0.14.0 there is one: the PDF reader painted a stroked
polyline whose points reach every corner of its bounding box (an `.ai`'s heat exchanger zigzag) as that box.

- **One patch per file**, named `<crate>--<what>.patch`, for one vendored crate of storytold/craft-libs, with
  craft-libs' paths (`vendor/<crate>/…`). Text before the first `diff --git` line is ignored: say there where the
  fix comes from (the pull request and its head commit) and when to remove it.
- **How it is applied.** `build.sh` reads the commit the tag's `Cargo.toml` pins for that crate in
  `[patch.crates-io]`, copies `vendor/<crate>` from craft-libs at that commit, applies the patch to the copy, and
  points that one line at the copy. Everything else stays on the pinned commit.
- **When the release has the fix**, `build.sh` says *already in craft-libs …: not applied, remove it*. Delete the
  patch, and say so in the README's *How this build differs*.

### When a patch stops

`build.sh` stops with *… fits neither craft-libs … nor its patched copy* when the pinned commit changed the code
the patch edits, and with *… has no single craft-libs line for …* when the tag no longer takes the crate from
craft-libs that way. Look whether the fix went in upstream in another form: open the `.ai` files with
`context/vc013/ai-ab.js` (the private runbook) in an official build. If it did, delete the patch. If not, take the
fix's current version from upstream, or rewrite the patch against the new commit, and build again.

## When debrand.py stops

`build/debrand.py` makes exact edits, and each one must match exactly once. When a release moves or rewrites that
code, the script stops and names what it could not find, before anything is built. That is on purpose: a build
must never go out with the ArtCraft name left in.

1. Find where the name is now, in a checkout of the release:

   ```bash
   grep -rni artcraft crates apps --include=*.rs --include=*.tsv --include=*.html | grep -v "/tests/"
   ```

2. Change the edits in `debrand.py` to match, keeping to the rules:
   - **Out:** the ArtCraft name, wordmark and mark anywhere a user sees them. That means menus, buttons, tooltips,
     About, and the translations.
   - **Out:** links to ArtCraft's community and website. A modified build must not send its users to them, as if
     ArtCraft supported it.
   - **Stays:** the plain sentence *Based on VectorCraft by the ArtCraft team*, which the brand terms allow, and the
     licence notices (NOTICE, LICENSE-*, the OFL texts).
   - **Stays:** the link to VectorCraft's source on GitHub.

   The terms are in VectorCraft's `docs/brand/LICENSE-brand.txt`.
3. Run `debrand.py` again. Its last lines list what is left in code, comments and tests aside. Only the
   attribution may be among them, plus constants that nothing uses any more.
4. Build, and run `check.py`.

## Local build setup

For WSL (Ubuntu 24.04), as root, once:

```bash
apt-get update && apt-get install -y build-essential pkg-config
curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable
. ~/.cargo/env
rustup target add wasm32-unknown-unknown
curl -fsSL https://github.com/trunk-rs/trunk/releases/download/v0.21.14/trunk-x86_64-unknown-linux-gnu.tar.gz | tar -xz -C ~/.cargo/bin
```

`build/build.sh` does the rest. It clones the tag and runs `debrand.py`. It fetches the official web zip for its
licence files. When that zip has a `fonts/` folder, it fetches craft-fonts at the commit the release's workflow pins
and builds with them, as the official web build did up to 0.12.0. From 0.13 the release builds its web version
without them, and so does this. Then it builds with `-C target-feature=+simd128` for the wasm target only. The work
folder needs about 5 GB.

Run `build.sh` from a WSL path or from `/mnt/c/...`. The scripts are kept LF by `.gitattributes`.

## When the official release gets SIMD

Check every new release's own web zip first:

```bash
python3 build/check.py path/to/unzipped/vectorcraft-web-X.Y.Z
```

If its SIMD line says PASS, the official build is as fast as this one. Then the site can host the official zip
unmodified again, which is simpler: the ArtCraft marks are allowed in an official build, so `debrand.py` is no longer
needed. To do that, bring back the workflow's earlier version, which downloaded the release's web zip and unpacked
it into `app/`; it is in the history from before 2026-10-17. Then update the README's *How this build differs*
section, and change `check.py`'s ArtCraft line to accept the official build.

## Why these choices

- **SIMD, not more.** wasm-opt at -O3 instead of the release's -Oz gave nothing measurable, so everything else
  stays as the release builds it.
- **Byte for byte.** `app/** -text` in `.gitattributes` keeps every file as built. The page names the loader and
  the wasm by SHA-384, and a line ending converted by Git on Windows would stop the editor.
- **A build of our own, not the official zip.** The official web release lacks SIMD. Measured on 10214's Maskin,
  a drag frame takes 11.5 ms in the official build and 5.0 ms in this one; at 1920 x 1080, 17.4 ms and 7.1 ms. The
  pixels are the same.
