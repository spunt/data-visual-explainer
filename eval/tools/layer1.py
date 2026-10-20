"""Extract the 'first layer' a skimming reader sees, identically for every condition.

Rule: rendered metric card -> text of the #gist section. Any other HTML/Markdown -> visible
text up to the second top-level section heading, capped at 300 words. Prints the word count.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class Text(HTMLParser):
    def __init__(self, start_id=None):
        super().__init__()
        self.start_id, self.depth, self.on, self.out, self.skip = start_id, 0, start_id is None, [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "svg", "textarea"):
            self.skip += 1
        if self.start_id and a.get("id") == self.start_id and not self.on:
            self.on, self.depth = True, 0
        if self.on and self.start_id:
            self.depth += 1
        if tag in ("p", "div", "li", "h1", "h2", "h3", "tr", "br"):
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg", "textarea"):
            self.skip -= 1
        if self.on and self.start_id:
            self.depth -= 1
            if self.depth == 0:
                self.on = False
                self.start_id = "__done__"

    def handle_data(self, d):
        if self.on and not self.skip:
            self.out.append(d)


def extract(path: Path) -> str:
    raw = path.read_text()
    if path.suffix == ".html" and 'id="gist"' in raw:
        p = Text("gist"); p.feed(raw); text = "".join(p.out)
    elif path.suffix == ".html":
        p = Text(); p.feed(raw); text = "".join(p.out)
        text = " ".join(text.split()[:300])
    else:
        parts = re.split(r"\n(?=#{1,2} )", raw)
        text = "\n".join(parts[:2])
        text = " ".join(text.split()[:300])
    return re.sub(r"\n\s*\n+", "\n", text).strip()


if __name__ == "__main__":
    t = extract(Path(sys.argv[1]))
    print(t)
    print(f"\n[words: {len(t.split())}]", file=sys.stderr)
