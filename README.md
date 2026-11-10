# IWMAC Vector

[VectorCraft](https://github.com/storytold/vectorcraft), an open-source vector editor by the ArtCraft team,
built from its official source and served from GitHub Pages for the
[IWMAC Designer Import/Export](https://github.com/Hapnes-dev/tampermonkey-scripts/tree/main/iwmac-designer-import-export)
userscript:

- **Editor:** https://hapnes-dev.github.io/iwmac-vector/app/
- **This page:** https://hapnes-dev.github.io/iwmac-vector/

Currently: VectorCraft 0.23.0.

## How this build differs from the official web build

Three things differ from the official web release of the same version, and nothing else.

- **The ArtCraft name is taken out.** VectorCraft's code is MIT OR Apache-2.0, but the ArtCraft name, wordmark
  and mark are trademarks, and
  [docs/brand/LICENSE-brand.txt](https://github.com/storytold/vectorcraft/blob/main/docs/brand/LICENSE-brand.txt)
  asks a published modified version to carry none of them. So
  [`build/debrand.py`](build/debrand.py) takes out:
  - the Discord button, and Discord in the Help menu and in the application menu (macOS's own);
  - the Help menu's ArtCraft website and getartcraft.com entries;
  - the translations that name ArtCraft.

  Help › About says the build is based on VectorCraft by the ArtCraft team. The link to VectorCraft's source on
  GitHub stays.
- **IWMAC objects keep their size.** The userscript marks with `data-iwdie-fixed="1"` the objects its Designer draws
  as a picture of their own size: pumps, alarms, LEDs, valves, arrows, values' pills. A resize would only cut them
  off or stretch them there. Here such an object moves and does nothing else. A selection of only such objects has
  no handles and no rotate zone, for the Selection tool and the shape tools alike. A scale or rotation of a selection that holds one, by handle, tool or the Transform panel, moves it by
  its centre and leaves its size and turn. This is [`build/patches/vectorcraft--iwdie-fixed-size.patch`](build/patches/vectorcraft--iwdie-fixed-size.patch),
  which `build.sh` applies to the release's source. It serves this site alone (UPDATING.md, *This site's own
  changes*).
- **The wasm ships gzipped.** GitHub refuses a file of 100 MiB or more, and VectorCraft's wasm passed 80 MiB in
  0.20.0, with no name or debug section left to strip. So [`build/compress-wasm.py`](build/compress-wasm.py) writes
  it as `vectorcraft-web-<hash>_bg.wasm.gz`, about 37 % of its size, and changes the page's loader. The loader unpacks
  the file as it downloads and compiles it meanwhile. It starts it only once its SHA-384 is the one the page was built
  with, the check the page's integrity attribute made before. A browser downloads the same bytes as before, since
  GitHub Pages already sent the wasm gzipped. A first load takes as long as before; a load from the browser's cache
  takes about a quarter of a second longer, for the unpacking and the check.

`build/patches/` can also carry a fix a release does not have yet, applied to the library at the commit the release
pins (UPDATING.md, *Fixes taken ahead of a release*). None is needed now. From 0.14.0 to 0.20.0 this site carried the PDF
reader's fix for a stroked polyline that reaches every corner of its bounding box, such as a heat exchanger's zigzag in
an `.ai`, which had opened as that box. 0.22.0 has the fix itself.

**WebAssembly SIMD** is no longer a difference. The official web release had none up to 0.22.0, and its canvas
renderer (vello_cpu) ran a scalar fallback, so from 0.11.0 to 0.22.0 this build added `-C target-feature=+simd128` for
the wasm target and drew about 2.3 times as fast. From 0.23.0 the release turns it on in its own `.cargo/config.toml`,
and `build.sh` uses that; it adds the flag only to a tag without it. `check.py` still checks the wasm for it.

Everything else is the official source at the release tag. The fonts are as in the official web build: craft-fonts
at the commit the release pins whenever its web zip carries them (up to 0.12.0, and again from 0.14.0), and none in
0.13. The licence files and notices come from the official web zip. The JavaScript the loader imports (`snippets/`)
and the app's icons (`icons/`), new in 0.20, are this build's own.

## What is here

| Path | What |
|---|---|
| `app/` | The editor: the page, its loader, the wasm (gzipped), the fallback fonts, and the official web zip's licence files and notices |
| `UPDATING.md` | The runbook for moving to a new VectorCraft release: try, check, test the userscript, publish, roll back |
| `build/build.sh` | Builds `app/` from a release tag: clones the tag, applies this site's own changes, runs `debrand.py`, applies the fixes in `build/patches/`, builds with SIMD (the release's own from 0.23.0, and craft-fonts where the official web build has them), adds the official zip's licence files |
| `build/patches/` | One patch per file: fixes taken ahead of a release, each to one vendored crate of craft-libs, and this site's own changes to VectorCraft (`vectorcraft--…`) |
| `build/debrand.py` | Takes the ArtCraft name out of a checkout. Every edit must match exactly once, so a release that moved the code stops the build instead of leaving the name in |
| `build/check.py` | Checks a build folder or the live site: integrity, SIMD, the ArtCraft name only in the attribution, the version, every file under GitHub's 100 MiB |
| `build/compress-wasm.py` | Ships the wasm gzipped, and makes the page unpack it and check its SHA-384 before it runs (`build.sh` runs it) |
| `build/bench-drawing.py` | Writes a made-up drawing shaped like an IWMAC panel, to time drags in two builds |
| `index.html` | A short landing page with the attribution |
| `.nojekyll` | Serve every file as it is (Pages would otherwise skip `_headers`) |
| `.github/workflows/update-vectorcraft.yml` | Run by hand: `build/build.sh` on GitHub's runner for a release tag, then a commit of `app/` |

## Updating VectorCraft

Follow **[UPDATING.md](UPDATING.md)**. In short:
1. Run Actions › *Update VectorCraft* with the release tag and **commit** unticked, to build it to try.
2. Check the artifact with `build/check.py`, look at it, and time it.
3. Test the userscript on it.
4. Run the workflow again with **commit** ticked.

The userscript drives VectorCraft from outside. It drops files, answers Save As by clicks, and catches the saved
download. A release can break that without breaking anything else, so test the userscript on a new build before it
goes live (UPDATING.md, step 5).

## Licences

VectorCraft is © the ArtCraft Team and the VectorCraft contributors, licensed [MIT](app/LICENSE-MIT) OR
[Apache-2.0](app/LICENSE-APACHE). The bundled fonts are under the SIL Open Font License (`app/OFL-*.txt`).

This site is based on VectorCraft by the ArtCraft team. It differs from the official build as described above.
It is not made, endorsed or supported by the ArtCraft team, and it carries none of the ArtCraft marks.
