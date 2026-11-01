"""Check a build of this site's VectorCraft before it goes live, or the live site after.

    python3 build/check.py app                                         a folder (app/ or a downloaded artifact)
    python3 build/check.py https://hapnes-dev.github.io/iwmac-vector/app/   the published site

What it checks, each line PASS, WARN or FAIL (any FAIL exits 1):
- the page names one loader (.js) and one wasm, and both match the SHA-384 the page gives them (integrity): a
  file changed after the build, line endings included, stops the editor from loading. Since 0.20.0 this site ships
  the wasm gzipped (build/compress-wasm.py): then it is unpacked and the unpacked wasm is checked, as the page does;
- every file is under GitHub's limit of 100 MiB a file (WARN from 80 MiB);
- WebAssembly SIMD: `simd128` in the wasm's target_features custom section;
- the ArtCraft name: only in the About box's attribution ("Based on VectorCraft by the ArtCraft team"), and no
  ArtCraft link (getartcraft.com, discord.gg/artcraft) left in the wasm;
- the version the wasm says it is (its "VectorCraft x.y.z" generator string);
- the UI font craft-fonts embeds (BIZ UDPGothic, looked for in UTF-16): WARN only, since a release may drop it;
- for a folder: the licence files (LICENSE-MIT, LICENSE-APACHE) are there, and VectorCraft's own README.md is not.
"""
import base64
import gzip
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
    packed = sorted(set(re.findall(r"vectorcraft-web-[0-9a-f]+_bg\.wasm\.gz", page)))
    wasms = packed or sorted(set(re.findall(r"vectorcraft-web-[0-9a-f]+_bg\.wasm", page)))
    if len(loaders) != 1 or len(wasms) != 1:
        say("FAIL", f"the page names {len(loaders)} loader(s) and {len(wasms)} wasm(s), not one of each")
        return
    files = {name: get(name) for name in (loaders[0], wasms[0])}
    sizes = dict((name, len(data)) for name, data in files.items())
    if packed:
        gz = files.pop(wasms[0])
        try:
            # a server that sends it with Content-Encoding: gzip has unpacked it already, as the page allows for
            files[wasms[0][:-3]] = gzip.decompress(gz) if gz[:2] == b"\x1f\x8b" else gz
            say("PASS", f"{wasms[0]} unpacks: {len(gz) / 1048576:.1f} MiB to {len(files[wasms[0][:-3]]) / 1048576:.1f} MiB")
        except OSError as e:
            say("FAIL", f"{wasms[0]} does not unpack: {e}")
            return
    for name, data in files.items():
        digest = "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()
        say("PASS" if digest in page else "FAIL", f"integrity of {name} ({len(data):,} bytes)")
    wasm = files[wasms[0][:-3] if packed else wasms[0]]

    if not url:
        sizes = {str(p.relative_to(root)): p.stat().st_size for p in root.rglob("*") if p.is_file()}
    big, size = max(sizes.items(), key=lambda kv: kv[1])
    mib = size / 1048576
    say("FAIL" if mib >= 100 else "WARN" if mib >= 80 else "PASS",
        f"largest file {big}: {mib:.1f} MiB (GitHub refuses a file of 100 MiB or more)")

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
