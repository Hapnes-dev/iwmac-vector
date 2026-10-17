"""Check a build of this site's VectorCraft before it goes live, or the live site after.

    python3 build/check.py app                                         a folder (app/ or a downloaded artifact)
    python3 build/check.py https://hapnes-dev.github.io/iwmac-vector/app/   the published site

What it checks, each line PASS, WARN or FAIL (any FAIL exits 1):
- the page names one loader (.js) and one .wasm, and both match the SHA-384 the page gives them (integrity): a
  file changed after the build, line endings included, stops the editor from loading;
- WebAssembly SIMD: `simd128` in the wasm's target_features custom section;
- the ArtCraft name: only in the About box's attribution ("Based on VectorCraft by the ArtCraft team"), and no
  ArtCraft link (getartcraft.com, discord.gg/artcraft) left in the wasm;
- the version the wasm says it is (its "VectorCraft x.y.z" generator string);
- the UI font craft-fonts embeds (BIZ UDPGothic, looked for in UTF-16): WARN only, since a release may drop it;
- for a folder: the licence files (LICENSE-MIT, LICENSE-APACHE) are there, and VectorCraft's own README.md is not.
"""
import base64
import hashlib
import pathlib
import re
import sys
import urllib.request

ATTRIBUTION = b"Based on VectorCraft by the ArtCraft team"
results = []


def say(level, text):
    results.append(level)
    print(f"{level:4}  {text}")


def target_features(wasm):
    """The wasm's target_features custom section, as a list like ['+simd128', ...]."""
    def leb(b, i):
        r = s = 0
        while True:
            x = b[i]
            i += 1
            r |= (x & 0x7F) << s
            s += 7
            if x < 0x80:
                return r, i
    i = 8
    while i < len(wasm):
        sid = wasm[i]
        i += 1
        size, i = leb(wasm, i)
        if sid == 0:
            nlen, j = leb(wasm, i)
            if wasm[j:j + nlen] == b"target_features":
                body = wasm[j + nlen:i + size]
                n, k = leb(body, 0)
                feats = []
                for _ in range(n):
                    pre = chr(body[k])
                    k += 1
                    ln, k = leb(body, k)
                    feats.append(pre + body[k:k + ln].decode())
                    k += ln
                return feats
        i += size
    return []


def main(where):
    url = re.match(r"https?://", where)
    if url:
        base = where if where.endswith("/") else where + "/"
        get = lambda name: urllib.request.urlopen(base + name + ("?check=1" if name == "index.html" else "")).read()
    else:
        root = pathlib.Path(where)
        get = lambda name: (root / name).read_bytes()

    page = get("index.html").decode("utf-8")
    loaders = sorted(set(re.findall(r"vectorcraft-web-[0-9a-f]+\.js", page)))
    wasms = sorted(set(re.findall(r"vectorcraft-web-[0-9a-f]+_bg\.wasm", page)))
    if len(loaders) != 1 or len(wasms) != 1:
        say("FAIL", f"the page names {len(loaders)} loader(s) and {len(wasms)} wasm(s), not one of each")
        return
    files = {name: get(name) for name in (loaders[0], wasms[0])}
    for name, data in files.items():
        digest = "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()
        say("PASS" if digest in page else "FAIL", f"integrity of {name} ({len(data):,} bytes)")
    wasm = files[wasms[0]]

    feats = target_features(wasm)
    say("PASS" if "+simd128" in feats else "FAIL", "WebAssembly SIMD: " + (", ".join(feats) or "no target_features section"))

    named = wasm.count(b"ArtCraft")
    attributed = wasm.count(ATTRIBUTION)
    say("PASS" if named == attributed == 1 else "FAIL",
        f"'ArtCraft' {named} time(s) in the wasm, {attributed} of them the attribution (expected 1 and 1)")
    links = sum(wasm.count(s) for s in (b"getartcraft", b"discord.gg/artcraft", b"artcraft.com"))
    say("PASS" if links == 0 else "FAIL", f"ArtCraft links in the wasm: {links}")

    m = re.search(rb"VectorCraft (\d+\.\d+\.\d+)", wasm)
    say("PASS" if m else "WARN", "version: " + (m.group(1).decode() if m else "no 'VectorCraft x.y.z' string found"))

    font = wasm.count("UDPGothic".encode("utf-16-be"))
    say("PASS" if font else "WARN", f"craft-fonts' UI font (BIZ UDPGothic) embedded: {'yes' if font else 'no'}")

    if not url:
        for name in ("LICENSE-MIT", "LICENSE-APACHE"):
            say("PASS" if (root / name).is_file() else "FAIL", f"{name} present")
        say("PASS" if not (root / "README.md").exists() else "FAIL", "VectorCraft's own README.md left out")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
    bad = results.count("FAIL")
    print(f"{len(results)} checks: {bad} failed, {results.count('WARN')} warning(s)")
    sys.exit(1 if bad else 0)
