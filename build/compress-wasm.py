"""Ship the editor's wasm gzipped, and have the page unpack it and check it before it runs.

GitHub refuses a file over 100 MiB, and VectorCraft's wasm passed 80 MiB in 0.20.0 (81.3 MiB, growing some 8 MiB in
three releases), with no name or debug section left to strip. Gzipped it is about 37 % of that (29.8 MiB for 0.20.0),
the same bytes a browser downloads from GitHub Pages today, which already sends the wasm with Content-Encoding: gzip.
Browsers unpack gzip in a page (DecompressionStream) but not brotli, so gzip it is.

    python3 build/compress-wasm.py <app folder>

It takes trunk's page and wasm as build.sh leaves them in app/ and:
- writes vectorcraft-web-<hash>_bg.wasm.gz (level 9, no file name or time stamp in it, so the same wasm always gives
  the same bytes) and deletes the .wasm;
- in index.html, preloads the .gz instead of the .wasm, and replaces trunk's init(...) of the wasm with a loader that
  fetches the .gz, unpacks it (unless a server already did, as Content-Encoding: gzip would), and checks its SHA-384
  against the one trunk wrote for the wasm before handing it to init: the integrity check the preload's SRI made.

Like debrand.py, every edit must match exactly once, so a trunk that writes its page differently stops the build
instead of shipping a page that cannot load its wasm.
"""
import base64
import gzip
import hashlib
import pathlib
import re
import sys


def main(app):
    page_path = app / "index.html"
    page = page_path.read_bytes().decode("utf-8")
    wasms = sorted(app.glob("vectorcraft-web-*_bg.wasm"))
    if len(wasms) != 1:
        sys.exit(f"{app}: expected one vectorcraft-web-*_bg.wasm, found {len(wasms)}")
    wasm = wasms[0]
    name, gz_name = wasm.name, wasm.name + ".gz"
    data = wasm.read_bytes()
    digest = "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()

    preload = re.compile(r'<link rel="preload" href="\./' + re.escape(name)
                         + r'" crossorigin="anonymous" integrity="(sha384-[A-Za-z0-9+/=]+)" as="fetch" type="application/wasm">')
    found = preload.findall(page)
    if len(found) != 1:
        sys.exit(f"index.html: expected one preload of {name}, found {len(found)}")
    if found[0] != digest:
        sys.exit(f"index.html: the preload's integrity is not {name}'s SHA-384")
    init = f"const wasm = await init({{ module_or_path: './{name}' }});"
    if page.count(init) != 1:
        sys.exit(f"index.html: expected one {init!r}, found {page.count(init)}")

    loader = (
        "// iwmac-vector: the wasm ships gzipped (GitHub refuses a file over 100 MiB; build/compress-wasm.py). It is unpacked\n"
        "// as it downloads (unless the server already did: then it does not start 1f 8b) and compiled meanwhile, and only\n"
        "// once its SHA-384 is the one this page was built with does init instantiate and start it.\n"
        "const wasm = await init({ module_or_path: await (async () => {\n"
        f"  const res = await fetch('./{gz_name}');\n"
        f"  if (!res.ok) throw new Error('{gz_name}: HTTP ' + res.status);\n"
        "  const reader = res.body.getReader(), first = await reader.read(), head = first.value || new Uint8Array(0);\n"
        "  let body = new ReadableStream({\n"
        "    start(c) { if (!first.done) c.enqueue(head); else c.close(); },\n"
        "    async pull(c) { const r = await reader.read(); if (r.done) c.close(); else c.enqueue(r.value); },\n"
        "  });\n"
        "  if (head[0] === 0x1f && head[1] === 0x8b) body = body.pipeThrough(new DecompressionStream('gzip'));\n"
        "  const [toCompile, toCheck] = body.tee();\n"
        "  const compiled = WebAssembly.compileStreaming(new Response(toCompile, { headers: { 'Content-Type': 'application/wasm' } }));\n"
        "  const bytes = await new Response(toCheck).arrayBuffer();\n"
        "  const sum = 'sha384-' + btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.digest('SHA-384', bytes))));\n"
        f"  if (sum !== '{digest}') throw new Error('{name}: not the wasm this page was built with');\n"
        "  return await compiled;\n"
        "})() });"
    )
    page = preload.sub(f'<link rel="preload" href="./{gz_name}" crossorigin="anonymous" as="fetch">', page)
    page = page.replace(init, loader)

    packed = gzip.compress(data, compresslevel=9, mtime=0)
    if gzip.decompress(packed) != data:
        sys.exit(f"{gz_name}: does not unpack to {name}")
    (app / gz_name).write_bytes(packed)
    page_path.write_bytes(page.encode("utf-8"))
    wasm.unlink()
    print(f"{name}: {len(data) / 1048576:.1f} MiB, shipped as {gz_name}: {len(packed) / 1048576:.1f} MiB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(pathlib.Path(sys.argv[1]))
