# IWMAC Vector

The official web build of [VectorCraft](https://github.com/storytold/vectorcraft), an
open-source vector editor, served from GitHub Pages for the
[IWMAC Designer Import/Export](https://github.com/Hapnes-dev/tampermonkey-scripts/tree/main/iwmac-designer-import-export)
userscript:

- **Editor:** https://hapnes-dev.github.io/iwmac-vector/app/
- **This page:** https://hapnes-dev.github.io/iwmac-vector/

## What is here

| Path | What |
|---|---|
| `app/` | `vectorcraft-web-0.10.0.zip` from the [v0.10.0 release](https://github.com/storytold/vectorcraft/releases/tag/v0.10.0), **unpacked and unmodified** — the page, its loader, the 62 MB `.wasm`, the bundled fallback fonts, and the licence files |
| `index.html` | A short landing page with the attribution |
| `.nojekyll` | Serve every file as it is (Pages would otherwise skip `_headers`) |
| `.github/workflows/update-vectorcraft.yml` | Run by hand to replace `app/` with another release |

The build is kept unmodified on purpose. Every change the userscript needs lives in the
userscript itself, which also runs on the editor's page:
- it drops the panel's background and drawing in as an SVG with layers;
- it catches the SVG you save and hands it back to the Designer tab through Tampermonkey's
  own storage.

Nothing leaves the browser.

## Updating VectorCraft

Actions → *Update VectorCraft* → *Run workflow* with a release tag (for example `v0.10.0`).
The workflow downloads that release's web zip, replaces `app/` and commits.

Test the bridge before relying on a new version. Two things it assumes:
- the editor opens a file dropped on its canvas;
- it saves through a blob download.

## Licences

VectorCraft is © the ArtCraft Team and the VectorCraft contributors, licensed
[MIT](app/LICENSE-MIT) OR [Apache-2.0](app/LICENSE-APACHE). The bundled CJK fonts are under
the SIL Open Font License (`app/OFL-*.txt`). This site is based on VectorCraft. It is not
made, endorsed or supported by the ArtCraft team, and it uses none of the ArtCraft marks
outside the unmodified official build.
