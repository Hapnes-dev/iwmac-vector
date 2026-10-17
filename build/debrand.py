"""Take the ArtCraft name out of a VectorCraft source checkout before it is built for this site.

VectorCraft's code is MIT OR Apache-2.0, but the ArtCraft name, wordmark and mark are trademarks under
docs/brand/LICENSE-brand.txt: a modified version that is published must not carry them. Building with
WebAssembly SIMD makes this site's copy such a version. So the parts of the app that use the ArtCraft name
are taken out:

- the Discord button (app bar, About, Home) and the Help menu's Discord, ArtCraft website and
  getartcraft.com entries, with their commands; the link to VectorCraft's source on GitHub stays;
- "Part of ArtCraft." in About, which now says the build is based on VectorCraft by the ArtCraft team;
- every translation line that holds the name.

Each change is an exact edit that must match once, so a new VectorCraft version that moved the code makes
this script stop with the place it could not find, instead of building with the name left in.

    python3 debrand.py <checkout>
"""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
ABOUT = ("Based on VectorCraft by the ArtCraft team, built with WebAssembly SIMD for the IWMAC Designer userscript. "
         "MIT OR Apache-2.0. Fonts: Source Sans 3, Inter, JetBrains Mono (OFL). Icons: Lucide (ISC) + VectorCraft.")


def edit(rel, pairs):
    p = root / rel
    s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            sys.exit(f"{rel}: expected one {old[:70]!r}, found {n}")
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")
    print("edited", rel)


# the app bar never shows the Discord button
edit("crates/ui-egui/src/chrome.rs", [("let discord = search && ", "let discord = false && search && ")])

# the button's tooltip, and About / Home: the GitHub link only
edit("crates/ui-egui/src/community.rs", [
    ('tl!("Join the ArtCraft community on Discord (discord.gg/artcraft)")', 'tl!("Discord")'),
    ("    discord_button(app, ui, true);\n    ui.add_space(8.0);\n", ""),
    ('    link(app, ui, "globe", tl!("ArtCraft website"), "help.website", &s("website"));\n', ""),
    ('    link(app, ui, "external-link", tl!("VectorCraft on getartcraft.com"), "help.appPage", &s("appPage"));\n', ""),
])

# the commands behind them
s = (root / "crates/engine/src/cmd/help.rs").read_text(encoding="utf-8")
cmds = [l for l in s.splitlines(keepends=True) if re.search(r'cmd!\(query "help\.(discord|website|appPage)"', l)]
if len(cmds) != 3:
    sys.exit(f"crates/engine/src/cmd/help.rs: expected the three community commands, found {len(cmds)}")
edit("crates/engine/src/cmd/help.rs", [(c, "") for c in cmds] + [
    ('Ok(json!({ "discord": DISCORD_URL, "website": WEBSITE_URL, "appPage": app_page_url(), "github": github_url() }))',
     'Ok(json!({ "github": github_url() }))'),
])

# the Help menu
edit("crates/ui-egui/src/menus.rs", [
    ('                c("Join Our Discord", "help.discord"),\n', ""),
    ('                c("ArtCraft Website", "help.website"),\n', ""),
    ('                c("VectorCraft on getartcraft.com", "help.appPage"),\n', ""),
])

# About
edit("crates/ui-egui/src/dialogs/about.rs", [
    ('"Part of ArtCraft. MIT OR Apache-2.0. Fonts: Source Sans 3, Inter, JetBrains Mono (OFL). Icons: Lucide (ISC) + VectorCraft."',
     '"' + ABOUT + '"'),
])

# the translations: every line holding the name goes (rows whose text is gone, and translators' notes)
n = 0
for p in sorted((root / "crates/ui-egui/src/i18n").glob("*.tsv")):
    lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    keep = [l for l in lines if "artcraft" not in l.lower()]
    if len(keep) != len(lines):
        p.write_text("".join(keep), encoding="utf-8")
        n += len(lines) - len(keep)
print("translation lines taken out:", n)

# what is left in the app's own sources (comments and tests aside) is listed for a look
left = []
for p in list((root / "crates").rglob("*.rs")) + list((root / "apps/vectorcraft-web").rglob("*")):
    if p.is_file() and p.suffix in (".rs", ".html", ".js", ".toml", ".tsv") and "/tests/" not in p.as_posix():
        for i, l in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            t = l.strip()
            if "artcraft" in l.lower() and not t.startswith(("//", "#", "///", "//!", "*")) and "assert" not in l:
                left.append(f"{p.relative_to(root).as_posix()}:{i}: {t[:150]}")
print("left in code (not comments, not asserts):", len(left))
for l in left:
    print("  ", l)
