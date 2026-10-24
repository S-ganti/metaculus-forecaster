"""
build_article.py - assemble the Sudan article into one self-contained HTML page.

    python reports/article_data.py     # recompute every chart's data from the model
    python reports/build_article.py    # -> reports/the-slow-arithmetic-of-hunger.html
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = HERE / "article"

FONTS = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800"
         "&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;"
         "0,8..60,600;1,8..60,400&display=swap")

page = "\n".join([
    "<title>The Slow Arithmetic of Hunger</title>",
    f'<link rel="preconnect" href="https://fonts.googleapis.com">',
    f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
    f'<link rel="stylesheet" href="{FONTS}">',
    "<style>\n" + (A / "style.css").read_text(encoding="utf-8") + "\n</style>",
    (A / "part1.html").read_text(encoding="utf-8"),
    (A / "part2.html").read_text(encoding="utf-8"),
    "<script>window.ARTICLE_DATA = " + (HERE / "article_data.json").read_text(encoding="utf-8") + ";</script>",
    "<script>\n" + (A / "charts.js").read_text(encoding="utf-8") + "\n</script>",
])
out = HERE / "the-slow-arithmetic-of-hunger.html"
out.write_text(page, encoding="utf-8")
print(f"wrote {out} ({len(page) / 1024:.0f} KB)")
