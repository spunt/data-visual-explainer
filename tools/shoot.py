"""Screenshot and interaction-test rendered cards with the local Chrome (Playwright, channel=chrome)."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/mc")
SITE = (Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent.parent / "site").resolve()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        for html in sorted(SITE.glob("*.html")):
            if html.name.endswith((".label.html", ".methods.html")) or html.name == "index.html":
                continue
            stem = html.stem
            pg = b.new_page(viewport={"width": 1280, "height": 900})
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(html.as_uri())
            pg.screenshot(path=str(OUT / f"{stem}-1-gist.png"))
            pg.locator("#build").scroll_into_view_if_needed()
            pg.evaluate("document.querySelector('.example').scrollIntoView()")
            pg.screenshot(path=str(OUT / f"{stem}-2-example.png"))
            for sid in ("who", "counts", "compare", "adjust", "sure"):
                el = pg.locator(f"#step-{sid}")
                if el.count():
                    pg.evaluate(f"window.scrollTo(0, document.querySelector('#step-{sid}').offsetTop - 300)")
                    pg.wait_for_timeout(500)
                    pg.screenshot(path=str(OUT / f"{stem}-2-step-{sid}.png"))
            pg.evaluate("document.querySelector('#mind').scrollIntoView()")
            pg.screenshot(path=str(OUT / f"{stem}-3-mind.png"))
            pg.evaluate("document.querySelector('#reproduce').scrollIntoView()")
            pg.screenshot(path=str(OUT / f"{stem}-4-reproduce.png"))
            pg.screenshot(path=str(OUT / f"{stem}-full.png"), full_page=True)
            # interactions: tooltip via keyboard, quiz, escape
            term = pg.locator(".term").first
            if term.count():
                term.focus()
                tip = pg.locator(".tip:not([hidden])")
                shown = tip.count() == 1
                pg.keyboard.press("Escape")
                hidden = pg.locator(".tip:not([hidden])").count() == 0
                print(f"{stem}: tooltip shows on focus={shown}, Escape hides={hidden}")
            q = pg.locator("fieldset.q").first
            if q.count():
                q.locator("input").first.check()
                print(f"{stem}: quiz feedback visible={q.locator('.why').is_visible()}")
            print(f"{stem}: page errors={errors or 'none'}")
            pg.close()
        for name in ("index.html",) + tuple(x.name for x in SITE.glob("*.label.html")):
            pg = b.new_page(viewport={"width": 1280, "height": 1100})
            pg.goto((SITE / name).as_uri())
            pg.screenshot(path=str(OUT / f"{name.replace('.html', '')}.png"), full_page=True)
            pg.close()
        b.close()


if __name__ == "__main__":
    main()
