"""Download the public inputs for the worked examples. Nothing here is redistributed in the repo.

Usage: python examples/fetch_data.py [minimum-wage|nhefs-ipw|all]

Each file is checked against the SHA-256 recorded when its card was written. A data file that
does not match stops the script, because the card's numbers would no longer be reproducible.
A document (paper, book) that does not match only warns: authors revise these in place.
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

MANIFEST = {
    "minimum-wage": [
        ("https://davidcard.berkeley.edu/data_sets/njmin.zip", "njmin.zip",
         "41a29aec6b489658b20030d044a2b20a5f5a04b871cde41df057afd6013ba587", "data"),
        ("https://davidcard.berkeley.edu/papers/njmin-aer.pdf", "njmin-aer.pdf",
         "6f9b9f1b6da9834c2a68bf86fc6078c83acdd7507db0d37b8b4814dfd2b3462e", "document"),
    ],
    "nhefs-ipw": [
        ("https://miguelhernan.org/s/nhefs.csv", "nhefs.csv",
         "6726827bfcebf7324d786211a517d0515532c2405cc71c5a1fab68d7116ea16c", "data"),
        ("https://miguelhernan.org/s/Rcode_WhatIf_part2.zip", "Rcode_WhatIf_part2.zip",
         "2b6eb0547d09cf8b6e86dcf8d8f6bcc9ddd030e7d4b7ea66a2c74f97332956f0", "data"),
        ("https://miguelhernan.org/s/hernanrobins_WhatIf_19aug26.pdf", "hernanrobins_WhatIf_19aug26.pdf",
         "a1067af923e9156bb95fbe4b0d18699bd0723e9c902bdc74465cf7782820b1b5", "document"),
    ],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(case: str) -> bool:
    dest = HERE / case / "data"
    dest.mkdir(parents=True, exist_ok=True)
    ok = True
    for url, name, digest, kind in MANIFEST[case]:
        target = dest / name
        if not target.exists():
            print(f"downloading {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "data-visual-explainer examples"})
            with urllib.request.urlopen(req, timeout=120) as r:
                target.write_bytes(r.read())
        actual = sha256(target)
        if actual != digest:
            msg = f"{target.name}: SHA-256 {actual[:12]}… differs from recorded {digest[:12]}…"
            if kind == "data":
                print(f"ERROR {msg}. The source changed; the card's numbers may no longer reproduce.")
                ok = False
            else:
                print(f"WARN  {msg}. The document was revised; check the cited passages still hold.")
        if name.endswith(".zip"):
            with zipfile.ZipFile(target) as z:
                z.extractall(dest)
    print(f"{case}: files in {dest.relative_to(HERE.parent)}")
    return ok


def main(argv: list[str]) -> int:
    which = argv[1] if len(argv) > 1 else "all"
    cases = list(MANIFEST) if which == "all" else [which]
    unknown = [c for c in cases if c not in MANIFEST]
    if unknown:
        print(f"unknown case {unknown[0]}; choose from {', '.join(MANIFEST)} or all")
        return 2
    return 0 if all([fetch(c) for c in cases]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
