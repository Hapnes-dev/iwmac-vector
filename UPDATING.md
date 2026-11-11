# Updating VectorCraft on this site

This is the runbook for moving https://hapnes-dev.github.io/iwmac-vector/app/ to a new VectorCraft release. The
build is made from the release's official source with three changes: the site's own patch, the wasm shipped gzipped,
and no ArtCraft name. Up to 0.22.0 it also added WebAssembly SIMD, which the release has itself from 0.23.0. The
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
- the canvas element `#vectorcraft_canvas`;
- the page's control channel, `window.vectorcraft`: its `request`, through which the userscript answers Save As
  (`ui.dialog.set`, `ui.dialog.confirm`).

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
| Every file is under 100 MiB (WARN from 80) | GitHub refuses a larger file. The wasm ships gzipped for that (`compress-wasm.py`), and `check.py` checks it unpacked |
| `simd128` is in the wasm's target features | The canvas draws about 2.3 times as fast with it. The release sets it itself from 0.23.0, and a build without it stops here |
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
- **Help.** It lists *VectorCraft on GitHub*, *Search Commands…*, *VectorCraft Help…*, *Safe Mode…* (from 0.23.0),
  *Check for Updates…* and *About VectorCraft*, with no ArtCraft entries.
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

**By hand, right after going live** (5 minutes, in the live Designer, on a test panel or one you will not save):
1. Open the panel in the IWMAC Designer and choose **Edit in VectorCraft**. If a card asks where the drawing comes
   from, take the plant's `.ai` or *Vectorize image*, and add the panel's objects when VectorCraft asks. The drawing
   and its objects open, and after a few seconds the IWMAC card in VectorCraft ends on a green line: *✓ Ready to
   sync*, or, for an `.ai`, that the panel's objects are on it. No Save As dialog stays on screen.
2. Move one object and press **Ctrl+S**. The card says *✓ Synced* with the time, the Designer *Background and IWMAC
   objects from VectorCraft*, and the object has moved on the panel.
3. Press Ctrl+Z in VectorCraft and Ctrl+S again, and the object is back. The panel's background is now the PNG the
   sync uploaded, under a name of its own (`<plant>_<panel>_<ddmmyy>.png`), so the plant's own picture is never
   written over. Do not save the panel: load it again (*Retrieve*, *Load*) and it is as it was. The uploaded PNG
   stays among the plant's pictures, unused.

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

### Known: VectorCraft 0.20.0, published with both patches carried over

Built, tested and published on 2026-11-01. 0.18.0 and 0.19.0 were never hosted.
- **The own patch no longer fitted.** 0.20.0 split `crates/doc/src/node.rs` and `crates/ui-egui/src/canvas.rs` into
  modules. The code the patch edits is unchanged, only moved: to `node/ops.rs`, `node/tests.rs` and
  `canvas/overlays.rs`. The patch was carried over by hand (`git apply --reject`, the four hunks placed again, the
  patch made again with its head kept). `vectorcraft-doc` passes 332 tests and `vectorcraft-tools` 767 with it,
  `fixed_objects_keep_their_size` among them. In the browser, a marked object shows no handles and keeps its size
  when dragged by a corner, as in 0.17.0.
- **debrand.py stopped too.** The menus moved to `crates/ui-egui/src/menus/tree.rs`, and its application menu (macOS's
  own, never shown in the in-window bar) lists Discord beside About. `debrand.py` now edits `menus/tree.rs` when it
  exists, that line included, and `menus.rs` before 0.20.
- **The heat exchanger.** The release still opens the zigzag as a rectangle, and the craft-libs commit it pins still
  lacks the fix, so the craft-libs patch stays; it applied unchanged. Every shape and every text of the test `.ai`
  files opens as in 0.17.0.
- **New in the package:** `snippets/` (JavaScript the loader imports) and `icons/`. `build.sh` copies this build's own,
  instead of leaving the official zip's.
- **SVG export writes shape elements.** From 0.19 a saved SVG holds `<rect>`, `<circle>`, `<ellipse>`, `<line>`,
  `<polyline>` and `<polygon>` where it held `<path>`. Compare two builds' SVGs by geometry, not by tag.
- **The canvas is 15 px narrower** (a new collapse bar on the right dock): Fit Artboard in Window gives 65.86 % instead
  of 66.93 % at 1400 x 900. Anything that maps document points to the screen by fixed numbers drifts; read the view
  from `window.vectorcraft.inspect()` (`canvasRect`, `view.zoom`, `view.center`) instead.
- **The userscript (1.107.6):** its syncs placed as many objects as on 0.17.0, the first save was answered by the
  clicks alone, and the IWMAC title stands where it stood in the menu bar, 12 px after Help.
- **Speed:** a full render after a zoom step on 10214's Maskin, 8.4 ms here, 8.4 ms in 0.17.0, 16.8 ms in the official
  0.20.0.
- **The wasm is 85.3 MB**, up from 76.7 MB in 0.17.0. GitHub refuses a file over 100 MB, and at this pace a release
  within a few weeks will reach it. Before then, decide how to serve it: the wasm compressed and unpacked by the page,
  or the site hosted where a large file is allowed (GitHub Pages does not serve Git LFS files).

### Known: VectorCraft 0.22.0, published without the craft-libs patch

Built, tested and published on 2026-11-08. 0.21.0 and 0.21.1 were never hosted.
- **The heat exchanger is fixed upstream.** 0.22.0 pins a craft-libs commit with upstream's own fix for the stroked
  polyline, stricter than ours: a five-point path counts as a rectangle only if it returns to its start and every step
  runs along one axis. `build.sh` met our patch with *fits neither*. The official 0.22.0 then opened the six test
  `.ai` files byte for byte as the patched 0.20.0 did, so the patch was deleted (*Fixes taken ahead of a release*).
- **The own patch** applied unchanged. With it, vectorcraft-doc passes 404 tests and vectorcraft-tools 850. In the
  browser a marked object shows no handles and keeps its size, as on 0.20.0. `debrand.py` ran unchanged.
- **The wasm** is 86.2 MiB and ships as 31.2 MiB gzipped, the first release built with `compress-wasm.py`.
- **`.ai` files:** our 0.22.0 opens all six test files byte for byte as the live 0.20.0, shapes and texts alike.
- **The userscript (1.115.0):** its syncs placed as many objects as on 0.20.0. The `.ai` flow gave the same results,
  its synced picture the same to the pixel. The first save was answered through VectorCraft's control channel. The
  IWMAC title stands 12 px after Help, and its menu opens with the same 175 rows.
- **In the live Designer** (step 5, the same day, the first time since 0.14.0): 2349's Maskin opened from the plant's
  `.ai`, with the panel's 58 objects added. One object moved and synced, then synced back, and the panel loaded
  again unchanged. A selected object showed no handles, as the own patch makes it.
- **Speed:** a full render after a zoom step on 10214's Maskin takes 8.4 ms, as in 0.20.0, against 16.7 ms in the
  official 0.22.0.
- **SIMD upstream:** the official web build gets WebAssembly SIMD after 0.22.0. This site keeps building its own, for
  its own patch; `+simd128` then only repeats what the release sets, and `check.py` keeps checking for it. Update the
  README's *How this build differs* when the official build has it.
- **Watch:** an open upstream change would name an opened file by its stem (`x.svg` opens as `x`) or by the title it
  carries. The userscript waits for the window title to be the file's name, so test that flow closely in the release
  that brings it.

### Known: VectorCraft 0.23.0, published with the own patch carried over

Built, tested and published on 2026-11-10.
- **SIMD is the release's own.** 0.23.0's `.cargo/config.toml` sets `-C target-feature=+simd128` for the wasm target,
  and its official web zip passes `check.py`'s SIMD line. `build.sh` now builds with the release's own flags and adds
  the flag only to a tag without it (*The official release has SIMD*). This build's target features are the official
  build's, one for one. A full render after a zoom step on 10214's Maskin takes 8.4 ms in this build, in the live
  0.22.0 and in the official 0.23.0 alike.
- **The own patch stopped on `select.rs`.** 0.23.0 gave the shape tools the Selection tool's rotate zone (`ROTATE_ZONE`
  and `rotate_zone`, beside `box_hit`), so that hunk no longer fitted; the other three files applied with offsets.
  The hunk was carried over by hand. `rotate_zone` got the same guard as `box_hit`, so a shape tool does not turn a
  selection of such objects either, as before 0.23.0, when shape tools had no rotate zone. With the patch,
  vectorcraft-doc passes 459 tests and vectorcraft-tools 894. A test of both guards, run on the clone and not kept in
  the patch, passed. In the browser a marked object shows no handles and keeps its size, byte for byte as in 0.22.0.
- **`debrand.py` stopped on the links of About and Home.** From 0.23.0 a link also takes a `centered` argument, for the
  Home screen's centred column, so it now takes the line either way, still exactly once. The start page shows no
  Discord button, only *Source code on GitHub*. Help gains *Safe Mode…*.
- **Colours from an `.ai` move again**, by up to 29 in a channel: 0.23.0 changed its Generic CMYK conversion. Every
  shape and text of the six test files opens as in 0.22.0, and this build opens them byte for byte as the official
  0.23.0. The new colours sit nearer the house's own pictures. On 2349's Maskin, against the plant's `2349_Maskin.png`
  (Illustrator's export), the mean largest-channel distance falls from 6.0 to 4.0, and 200,009 of the 207,616 changed
  pixels came nearer.
- **The userscript (1.115.3):** its syncs placed as many objects as on 0.22.0 (77, 107 and 77). The `.ai` flow gave the
  same results, its synced picture differing by those colours alone. The first save was answered through the control
  channel, which 0.23.0 builds from a shared library with the same methods. The IWMAC title stands 12 px after Help.
- **In the live Designer** (step 5, the same day, userscript 1.115.3): 2349's Maskin opened from the drawing its picture
  keeps, with the panel's objects on top. The card ended on *✓ Ready to sync*, and no Save As stayed on screen. One
  object moved and synced (*✓ Synced · 1 changed*, 1 of 59 objects moved), then synced back, and the panel loaded
  again unchanged. The synced picture came out 1280 × 1024 instead of the 1400 × 750 of the picture it came from.
  2349's Designer canvas is 1280 × 1024, and userscript 1.115.3 fitted the kept drawing into it, scaled down. That was
  the userscript's own layout, not VectorCraft's. Run again with userscript 1.116.0, the drawing stayed at its own
  size. The picture is still the canvas's 1280 × 1024, the part the Designer shows (it clips a wider picture at its
  canvas), and there it matches the saved one.
- **The wasm** is 93.7 MiB, shipped as 34.1 MiB gzipped. The official one, 93.8 MiB raw, is just under GitHub's limit.
- **Nothing to do:** the new progress window for a slow open shows on the desktop only, since the web opens files at
  once; and an `.ai` with editing data no longer shows the Import PDF dialog, which the userscript never answered.
- **Watch:** the upstream change that would name an opened file by its stem or by its title is still open.

### Known: VectorCraft 0.24.0, published as it came

Built, tested and published on 2026-11-11.
- **Nothing to carry over.** The own patch applied with small offsets, and `debrand.py` ran unchanged: the same six
  lines left for a look, and 155 translation lines taken out. With the patch, vectorcraft-doc passes 474 tests and
  vectorcraft-tools 920. A test of both guards, run on the clone, passed. In the browser a marked object shows no
  handles and keeps its size, byte for byte as in 0.23.0.
- **`.ai` files.** This build opens the six test files byte for byte as the official 0.24.0, and five of them byte for
  byte as 0.23.0. The sixth is 2313's VGV: three clips that cut nothing are gone, and the 40 % opacity they sat in now
  rests on their lines. Rendered, no pixel differs from 0.23.0's by more than 8, and the lines match the house's own
  picture as before.
- **The userscript (1.119.0):** its syncs placed as many objects as on 0.23.0. The `.ai` flow gave the same results and
  the same synced picture to the pixel. The first save was answered through the control channel. The IWMAC title
  stands 12 px after Help.
- **In the live Designer** (step 5, the same day, userscript 1.119.0): 2349's Maskin opened from the drawing its picture
  keeps, on a 1400 × 750 artboard, the panel's own size. The card ended on *✓ Ready to sync*, and no Save As stayed on
  screen. One object moved and synced (*✓ Synced · 1 changed*), then synced back, and the panel loaded again
  unchanged. The synced picture matched the saved one (mean difference 0.12). Moved and moved back, that object came
  back 1 px right of where it was. That is on the userscript's side: both builds save the drawing byte for byte the
  same, before the move and after it. Userscript 1.119.1 puts a placeholder that is back within a pixel of where it was
  sent exactly there.
- **Speed:** a full render after a zoom step on 10214's Maskin takes 8.4 ms here, in 0.23.0 and in the official 0.24.0.
- **The wasm** is 96.7 MiB, shipped as 35.2 MiB gzipped. The official raw wasm is 96.8 MiB, 3.2 MiB under GitHub's
  limit, and it grows with every release: this release adds seven built-in symbol, brush and style libraries.
- **Watch:** the upstream change that would name an opened file by its stem or by its title is still open.

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
fix can go in `build/patches/` until a release has it. None is needed now. From 0.14.0 to 0.20.0 there was one,
`hayro-interpret--polyline-not-a-rectangle.patch`: the PDF reader painted a stroked polyline whose points reach every
corner of its bounding box (an `.ai`'s heat exchanger zigzag) as that box. 0.22.0 has upstream's own fix, which
`build.sh` met with *fits neither*. The official 0.22.0 then opened the test `.ai` files byte for byte as the patched
0.20.0 did, so the patch was deleted. It is in the history if a release ever needs it again.

- **One patch per file**, named `<crate>--<what>.patch`, for one vendored crate of storytold/craft-libs, with
  craft-libs' paths (`vendor/<crate>/…`). Text before the first `diff --git` line is ignored: say there where the
  fix comes from (the pull request and its head commit) and when to remove it.
- **How it is applied.** `build.sh` reads the commit the tag's `Cargo.toml` pins for that crate in
  `[patch.crates-io]`, copies `vendor/<crate>` from craft-libs at that commit, applies the patch to the copy, and
  points that one line at the copy. Everything else stays on the pinned commit.
- **When the release has the fix**, `build.sh` says *already in craft-libs …: not applied, remove it*. Delete the
  patch, and say so in the README's *How this build differs*.

## This site's own changes

Some changes serve the userscript alone and will never be in a release. Each is a patch to VectorCraft's own source
in `build/patches/`, named `vectorcraft--<what>.patch`, with the release's paths (`crates/…`). `build.sh` applies it
to the clone of the tag before `debrand.py` runs. Text before the first `diff --git` line says what it does and why.
Keep these patches for every release.

Since 2026-10-29 there is one: `vectorcraft--iwdie-fixed-size.patch`, *objects that keep their size*. The userscript
marks with `data-iwdie-fixed="1"` the IWMAC objects its Designer draws as a picture of their own size, such as
pumps, alarms and values' pills. VectorCraft keeps that mark as it keeps any `data-*` attribute. With the patch:
- the Selection tool shows a selection of only such objects no handles and no rotate zones;
- any transform moves such an object by its centre and leaves its size and turn. This covers a scale or rotation of
  a selection that holds one, the Transform panel's width, and the Scale and Rotate tools;
- a group that holds just one such object keeps its size too.

Its test is `fixed_objects_keep_their_size` in `crates/doc/src/node.rs`. To run it with the doc and tools crates'
tests, apply the patch to a clone of the tag, then run `cargo test -p vectorcraft-doc --lib` and
`cargo test -p vectorcraft-tools --lib`.

### When a patch stops

`build.sh` stops with *… does not fit vX.Y.Z* when a release changed the code a `vectorcraft--` patch edits. Apply
it to a clone of the tag by hand (`git apply --reject`), rewrite what was rejected against the new code, and make
the patch again with `git diff`, its head kept. Then run its test and build again.

For a craft-libs patch, `build.sh` stops with *… fits neither craft-libs … nor its patched copy* when the pinned commit changed the code
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
without them, and so does this. Then it builds with WebAssembly SIMD for the wasm target: from 0.23.0 by the
release's own `.cargo/config.toml`, and for an earlier tag by `-C target-feature=+simd128`, which it adds then. The
work folder needs about 5 GB.

Run `build.sh` from a WSL path or from `/mnt/c/...`. The scripts are kept LF by `.gitattributes`.

## The official release has SIMD

From 0.23.0 the official web release is built with WebAssembly SIMD: the release's `.cargo/config.toml` sets
`-C target-feature=+simd128` for the wasm target, as this site did from 0.11.0. `check.py` on its zip says PASS on
the SIMD line. `build.sh` then builds with the release's own flags. It sets the flag itself only for a tag whose
config lacks it, because an environment variable of the same key could replace whatever else the release puts there.
`check.py` still fails a build without SIMD, so a release that drops it stops the update.

This site still builds its own, and cannot host the official zip unmodified again:
- its own patch (*This site's own changes*) needs the source;
- the official wasm is as large as this one, so it still has to ship gzipped, and `compress-wasm.py` changes the page.
  A page changed that way is a modified build, so `debrand.py` stays (the brand terms).

## Why these choices

- **SIMD, not more.** wasm-opt at -O3 instead of the release's -Oz gave nothing measurable, so everything else
  stays as the release builds it.
- **The wasm gzipped, not split or hosted elsewhere.** GitHub refuses a file of 100 MiB or more, GitHub Pages does not
  serve Git LFS files (only their pointers), and Cloudflare Pages takes no file over 25 MiB. gzip, not brotli: brotli
  makes 0.20.0's wasm 18.2 MiB instead of 29.8 MiB, but browsers unpack only gzip and deflate in a page (Chrome 156's
  DecompressionStream has no brotli or zstd), and a brotli decoder in JavaScript would be more of our own code, and
  slower. Measured on 0.20.0 in Chrome, cold loads, against the raw wasm sent gzipped as Pages sends it: 2979 ms
  against 2952 at 100 Mbit/s, 8910 against 8953 at 30 Mbit/s; from the browser's cache 554 ms against 285 (unpacking
  306 ms and the SHA-384 156 ms, partly in parallel). A server that unpacks the file itself (Content-Encoding: gzip)
  is handled: the page sees the wasm's own first bytes and skips the unpacking.
- **Byte for byte.** `app/** -text` in `.gitattributes` keeps every file as built. The page names the loader and
  the wasm by SHA-384, and a line ending converted by Git on Windows would stop the editor.
- **A build of our own, not the official zip.** It began for SIMD, which the official web release lacked up to 0.22.0:
  measured on 10214's Maskin, a drag frame took 11.5 ms in the official build and 5.0 ms in this one; at 1920 x 1080,
  17.4 ms and 7.1 ms, with the same pixels. From 0.23.0 the release has SIMD itself, and the build stays our own for
  the site's patch and for the gzipped wasm (*The official release has SIMD*).
