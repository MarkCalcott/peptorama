#!/usr/bin/env python3
"""
inline_bigscape_ui.py — turn a BiG-SCAPE 2 output directory into ONE
self-contained .html file that opens straight from disk.

    python inline_bigscape_ui.py bs_out/combined -o bigscape_combined_ui.html

Why this is needed
------------------
BiG-SCAPE writes index.html plus a ./html_content tree (14 JS, 2 CSS, 8 images)
and keeps the results in a separate SQLite file. The page only loads that
database automatically when it is served from localhost -- it does
`XHR GET /data_sqlite.db`, which a file:// page cannot satisfy. Opened by
double-click it therefore comes up empty and waits for you to pick the .db by
hand, and emailing the directory tends to lose html_content/ anyway.

This script inlines the CSS, the JS (in reference order), the images as data
URIs, and the database itself as base64, then replaces the localhost/XHR branch
with a decode of the embedded bytes. The manual file-picker is left in place, so
a different run's .db can still be loaded into the same page.
"""
import os, re, base64, argparse, mimetypes

MIME = {".png": "image/png", ".gif": "image/gif", ".jpg": "image/jpeg"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir", help="a BiG-SCAPE output dir (holds index.html)")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--db", default=None,
                    help="SQLite file to embed; default: the *.db in rundir")
    a = ap.parse_args()

    html = open(os.path.join(a.rundir, "index.html"), encoding="utf-8").read()
    db = a.db or next(os.path.join(a.rundir, f) for f in sorted(os.listdir(a.rundir))
                      if f.endswith(".db"))

    # ---- CSS -> <style>
    def css_sub(m):
        p = os.path.join(a.rundir, m.group(1).lstrip("./"))
        return f"<style>\n/* {m.group(1)} */\n{open(p, encoding='utf-8').read()}\n</style>"
    html = re.sub(r'<link[^>]+href="(\./html_content/css/[^"]+)"[^>]*>', css_sub, html)

    # ---- JS -> <script>, preserving reference order
    def js_sub(m):
        p = os.path.join(a.rundir, m.group(1).lstrip("./"))
        src = open(p, encoding="utf-8", errors="replace").read()
        # a stray </script> inside a bundle would close the tag early
        src = src.replace("</script>", "<\\/script>")
        return f"<script>\n/* {m.group(1)} */\n{src}\n</script>"
    html = re.sub(r'<script[^>]+src="(\./html_content/js/[^"]+)"[^>]*>\s*</script>',
                  js_sub, html)

    # ---- images -> data URIs
    def img_sub(m):
        rel = m.group(1)
        p = os.path.join(a.rundir, rel.lstrip("./"))
        ext = os.path.splitext(p)[1].lower()
        mime = MIME.get(ext) or mimetypes.guess_type(p)[0] or "application/octet-stream"
        b64 = base64.b64encode(open(p, "rb").read()).decode()
        return f'src="data:{mime};base64,{b64}"'
    html = re.sub(r'src="(\./html_content/img/[^"]+)"', img_sub, html)

    # ---- database -> base64, replacing the localhost-only XHR branch
    raw = open(db, "rb").read()
    b64 = base64.b64encode(raw).decode()
    old = re.search(r'\n    if \(location\.hostname === "localhost".*?\n    \} else \{'
                    r'\n        showLoading\(true, false\);\n    \}', html, re.S)
    if not old:
        raise SystemExit("could not find the localhost/XHR block to replace; "
                         "BiG-SCAPE's index.html layout has changed")
    new = ('\n    // Embedded database (inline_bigscape_ui.py). The original code\n'
           '    // XHR-fetched /data_sqlite.db, which only works when served from\n'
           '    // localhost; a file:// page got an empty UI. The file picker below\n'
           '    // still works for loading a different run.\n'
           '    initSqlJs().then(function (SQL) {\n'
           '        const b64 = EMBEDDED_DB_B64;\n'
           '        const bin = atob(b64);\n'
           '        const arr = new Uint8Array(bin.length);\n'
           '        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);\n'
           '        window.db = new SQL.Database(arr);\n'
           '        try { dataLoaded() } catch (err) { sendError(err.message) }\n'
           f'        $("#status").html("Loaded: {os.path.basename(db)} (embedded)")\n'
           '    })')
    html = html[:old.start()] + new + html[old.end():]
    html = html.replace("<head>", "<head>\n<script>\nconst EMBEDDED_DB_B64 = \""
                        + b64 + "\";\n</script>", 1)

    open(a.out, "w", encoding="utf-8").write(html)
    left = re.findall(r'(?:src|href)="\./html_content/[^"]+"', html)
    print(f"wrote {a.out}  {os.path.getsize(a.out)/1e6:.1f} MB")
    print(f"embedded db: {os.path.basename(db)} ({len(raw)/1e6:.1f} MB)")
    print(f"unresolved local references remaining: {len(left)}")
    if left:
        print("  " + "\n  ".join(sorted(set(left))))


if __name__ == "__main__":
    main()
