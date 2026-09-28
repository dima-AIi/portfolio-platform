from xml.sax.saxutils import escape

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def render_sitemap(urls: list[tuple[str, str | None]]) -> str:
    """Render a minimal, valid sitemap.xml document.

    Built with the stdlib on purpose: pulling in a template engine for a file
    this small would not be worth the dependency.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<urlset xmlns="{SITEMAP_NS}">',
    ]
    for loc, lastmod in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(loc)}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{escape(lastmod)}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"
