# IWMAC Vector

[VectorCraft](https://github.com/storytold/vectorcraft), an open-source vector editor by the ArtCraft team,
built from its official source and served from GitHub Pages for the
[IWMAC Designer Import/Export](https://github.com/Hapnes-dev/tampermonkey-scripts/tree/main/iwmac-designer-import-export)
userscript:

- **Editor:** https://hapnes-dev.github.io/iwmac-vector/app/
- **This page:** https://hapnes-dev.github.io/iwmac-vector/

Currently: VectorCraft 0.14.0.

## How this build differs from the official web build

Three things differ from the official web release of the same version, and nothing else.

- **WebAssembly SIMD is on.** The official web release is built without it: its wasm's `target_features` lack
  `simd128`, and the canvas renderer (vello_cpu) then runs its scalar fallback. This build adds
  `-C target-feature=+simd128` for the wasm target only. The canvas then draws about 2.3 times as fast. These are
  the render times VectorCraft 0.11.0 shows in its status bar while one object is dragged, in Chrome:

  | Drawing | Window | Official | This build |
  |---|---|---|---|
  | 10214's Maskin (about 900 elements) | 1400 × 900 | 11.6 ms | 5.0 ms |
  | the same | 1920 × 1080 | 16.8 ms | 7.0 ms |
  | 10214's Oversikt | 1400 × 900 | 12.8 ms | 5.5 ms |

  The pixels it draws are the same. At fit zoom they are identical, and at 186 % 0.04 % of them differ, by at
  most 2/255.
- **The ArtCraft name is taken out.** VectorCraft's code is MIT OR Apache-2.0, but the ArtCraft name, wordmark
  and mark are trademarks, and
  [docs/brand/LICENSE-brand.txt](https://github.com/storytold/vectorcraft/blob/main/docs/brand/LICENSE-brand.txt)
  asks a published modified version to carry none of them. So
  [`build/debrand.py`](build/debrand.py) takes out:
  - the Discord button;
  - the Help menu's ArtCraft website and getartcraft.com entries;
  - the translations that name ArtCraft.

  Help › About says the build is based on VectorCraft by the ArtCraft team. The link to VectorCraft's source on
  GitHub stays.
- **Fixes taken ahead of a release.** A fix that VectorCraft or its libraries have not released yet, when a release
  breaks something the userscript's drawings need. Each is a patch in [`build/patches/`](build/patches/), with where
  it comes from at its head. `build.sh` applies it to the library at the commit the release pins, and stops the
  build when it no longer fits. Now one: since 0.12.0 the PDF reader opens a stroked polyline whose points reach
  every corner of its bounding box, such as a heat exchanger's zigzag in an `.ai`, as that box.

Everything else is the official source at the release tag. The fonts are as in the official web build: craft-fonts
at the commit the release pins whenever its web zip carries them (up to 0.12.0, and again from 0.14.0), and none in
0.13. The licence files
and notices come from the official web zip.

## What is here

| Path | What |
|---|---|
| `app/` | The editor: the page, its loader, the `.wasm`, the fallback fonts, and the official web zip's licence files and notices |
| `UPDATING.md` | The runbook for moving to a new VectorCraft release: try, check, test the userscript, publish, roll back |
| `build/build.sh` | Builds `app/` from a release tag: clones the tag, runs `debrand.py`, applies `build/patches/`, builds with SIMD (and craft-fonts where the official web build has them), adds the official zip's licence files |
| `build/patches/` | Fixes taken ahead of a release, one patch per file, each to one vendored crate of craft-libs |
| `build/debrand.py` | Takes the ArtCraft name out of a checkout. Every edit must match exactly once, so a release that moved the code stops the build instead of leaving the name in |
| `build/check.py` | Checks a build folder or the live site: integrity, SIMD, the ArtCraft name only in the attribution, the version |
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
