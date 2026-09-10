"""Normalise pages exported from the collectd GitHub wiki.

The export uses Gollum's link syntax (``[Text](Target "wikilink")``) and points
at a lot of pages and URLs that no longer resolve. This module rewrites what it
can, degrades the rest to plain text, and records every unresolved reference so
the build can report on it.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path


#: Given a wiki page stem, return a site-relative URL or ``None``.
Resolver = Callable[[str], str | None]


WIKILINK = re.compile(r'\[([^\]]*?)\]\(([^)]*?)\s+"wikilink"\)')
IMAGE = re.compile(r'!\[([^\]]*?)\]\(([^)\s"]+)(?:\s+"[^"]*")?\)')
MARKDOWN_LINK = re.compile(r'(?<!\!)\[([^\]]*?)\]\((https?://[^)\s]+)(?:\s+"[^"]*")?\)')
BARE_HEADER_ROW = re.compile(r'^\|.*\|\s*$')

# Roughly a third of the wiki pages were exported with raw HTML tables and
# anchors rather than Markdown, so both spellings have to be handled.
HTML_WIKILINK = re.compile(r'<a href="([^"]*?)"\s+title="wikilink">(.*?)</a>', re.DOTALL)
HTML_TABLE = re.compile(r'<table>.*?</table>\s*', re.DOTALL)
#: Keys that identify a table as a plugin infobox rather than page content.
INFOBOX_KEYS = {
    'name',
    'type',
    'callbacks',
    'status',
    'firstversion',
    'copyright',
    'license',
    'manpage',
    'see also',
}
HTML_ROW = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL)
HTML_CELL = re.compile(r'<(?:th|td)[^>]*>(.*?)</(?:th|td)>', re.DOTALL)
HTML_TAG = re.compile(r'<[^>]+>')
HTML_PARA_SPLIT = re.compile(r'</p>\s*<p>')
HTML_PARA_WRAP = re.compile(r'</?p>')

#: Old collectd.org URLs, all of which now 404 or redirect to the front page.
LEGACY_WIKI_URL = re.compile(
    r'https?://(?:www\.)?collectd\.org/wiki/index\.php'
    r'(?:/(?:Plugin:)?(?P<path>[A-Za-z0-9_:%.\-]+)'
    r'|\?title=(?:Plugin:)?(?P<query>[A-Za-z0-9_:%.\-]+))'
)
LEGACY_MANPAGE_URL = re.compile(
    r'https?://(?:www\.)?collectd\.org/documentation/manpages/'
    r'(?P<page>[a-z0-9.\-_]+?)(?:\.(?P<section>\d))?\.s?html'
    r'(?:#(?P<anchor>[A-Za-z0-9_\-]+))?'
)

#: A URL sitting on its own in the text, rather than inside [label](url).
BARE_URL = re.compile(r'(?<![(\[<"])\bhttps?://[^\s)<>"\]]+')
HTML_HREF = re.compile(r'<a href="(https?://[^"]+)">(.*?)</a>', re.DOTALL)


@dataclass
class Metadata:
    """The infobox table at the top of most wiki plugin pages."""

    fields: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        """Look up an infobox field, tolerating the wiki's casing and trailing colons."""
        return self.fields.get(key.lower().rstrip(':'))


@dataclass
class Conversion:
    """One wiki page rewritten for this site, plus what could not be resolved."""

    body: str
    metadata: Metadata
    images: set[str] = field(default_factory=set)
    unresolved: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _Rewrite:
    """What every rewriter below needs: where to record, and how to resolve."""

    result: Conversion
    resolve: Resolver
    manpage_anchor: Callable[[str, str | None], str | None] | None
    has_image: Callable[[str], bool] | None


def strip_tags(html: str) -> str:
    """Reduce an HTML fragment to its text."""
    return HTML_TAG.sub('', html).replace('&amp;', '&').strip()


def split_html_metadata(text: str) -> tuple[Metadata, str] | None:
    """Pull a leading infobox written as a raw HTML table."""
    table = HTML_TABLE.search(text)
    if not table or table.start() > 4000:
        return None

    fields: dict[str, str] = {}
    for row in HTML_ROW.findall(table.group(0)):
        cells = HTML_CELL.findall(row)
        if len(cells) != 2:
            continue
        key = strip_tags(cells[0]).strip('*: ').lower()
        if key:
            value = HTML_PARA_SPLIT.sub(', ', cells[1].strip())
            fields[key] = HTML_PARA_WRAP.sub('', value).strip()

    if len(fields) < 3 or not fields.keys() & INFOBOX_KEYS:
        return None  # a content table, not an infobox

    body = text[: table.start()] + text[table.end() :]
    return Metadata(fields), body.lstrip('\n')


def split_metadata(text: str) -> tuple[Metadata, str]:
    """Pull the leading two-column infobox table off a wiki page."""
    if html := split_html_metadata(text):
        return html

    lines = text.splitlines()
    if not lines or not BARE_HEADER_ROW.match(lines[0]):
        return Metadata(), text

    fields: dict[str, str] = {}
    index = 0
    for index, line in enumerate(lines):  # noqa: B007 -- `index` is read after the loop
        if not BARE_HEADER_ROW.match(line):
            break
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells) != 2 or set(cells[0]) <= set('- '):
            continue
        key = cells[0].strip('*: ').lower()
        if key:
            fields[key] = cells[1].strip()
    else:
        index = len(lines)

    return Metadata(fields), '\n'.join(lines[index:]).lstrip('\n')


# The rating sums the seven nested rewriters below; each one is small.


def rewrite_image(ctx: _Rewrite, match: re.Match[str]) -> str:
    """Rewrite one image reference, dropping it when the file is not in the wiki."""
    alt, target = match.group(1), match.group(2)
    if target.startswith(('http://', 'https://')):
        return match.group(0)
    if ctx.has_image is not None and not ctx.has_image(target):
        ctx.result.unresolved.append(f'image: {target}')
        return ''
    ctx.result.images.add(target)
    return f'![{alt}](../assets/wiki/{target})'


def rewrite_wikilink(ctx: _Rewrite, match: re.Match[str]) -> str:
    """Rewrite one Gollum wikilink, degrading to plain text when unresolved."""
    label, target = match.group(1), match.group(2)
    target = target.split('#')[0].replace(' ', '-')
    url = ctx.resolve(target)
    if url is None:
        ctx.result.unresolved.append(target)
        return label
    return f'[{label}]({url})'


def rewrite_html_wikilink(ctx: _Rewrite, match: re.Match[str]) -> str:
    """Rewrite one wikilink that was exported as a raw HTML anchor."""
    target, label = match.group(1), strip_tags(match.group(2))
    url = ctx.resolve(target.split('#')[0].replace(' ', '-'))
    if url is None:
        ctx.result.unresolved.append(target)
        return label
    return f'<a href="{url}">{label}</a>'


def internal_url_for(ctx: _Rewrite, url: str) -> tuple[str, str] | None:
    """Map an old collectd.org URL onto this site, with a fallback label."""
    if legacy := LEGACY_WIKI_URL.fullmatch(url):
        page = legacy.group('path') or legacy.group('query')
        page = page.replace('%20', '-').replace(':', '-').replace('_', '-')
        for candidate in (page, f'Plugin-{page}'):
            if internal := ctx.resolve(candidate):
                return internal, page.replace('-', ' ')
        return None

    if legacy := LEGACY_MANPAGE_URL.fullmatch(url):
        if ctx.manpage_anchor is None:
            return None
        page, section = legacy.group('page'), legacy.group('section')
        internal = ctx.manpage_anchor(page, legacy.group('anchor'))
        if internal is None:
            return None
        return internal, f'{page}({section})' if section else page

    return None


def rewrite_external_link(ctx: _Rewrite, match: re.Match[str]) -> str:
    """Remap an old collectd.org link onto this site, or leave it as it is."""
    label, url = match.group(1), match.group(2)
    if target := internal_url_for(ctx, url):
        return f'[{label}]({target[0]})'
    if LEGACY_WIKI_URL.fullmatch(url) or LEGACY_MANPAGE_URL.fullmatch(url):
        ctx.result.unresolved.append(url)
        return label
    return match.group(0)


def rewrite_bare_url(ctx: _Rewrite, match: re.Match[str]) -> str:
    """Remap an old collectd.org URL that sits bare in the text."""
    url = match.group(0)
    trailing = ''
    while url and url[-1] in '.,;:':
        trailing, url = url[-1] + trailing, url[:-1]
    if target := internal_url_for(ctx, url):
        return f'[{target[1]}]({target[0]}){trailing}'
    return match.group(0)


def rewrite_html_href(ctx: _Rewrite, match: re.Match[str]) -> str:
    """Remap an old collectd.org link written as a raw HTML anchor."""
    url, label = match.group(1), match.group(2)
    if target := internal_url_for(ctx, url):
        return f'<a href="{target[0]}">{label}</a>'
    return match.group(0)


def rewrite_all(ctx: _Rewrite, source: str) -> str:
    """Apply every rewrite, in order, to one chunk of wiki Markdown."""
    source = HTML_WIKILINK.sub(partial(rewrite_html_wikilink, ctx), source)
    source = HTML_HREF.sub(partial(rewrite_html_href, ctx), source)
    source = IMAGE.sub(partial(rewrite_image, ctx), source)
    source = WIKILINK.sub(partial(rewrite_wikilink, ctx), source)
    source = MARKDOWN_LINK.sub(partial(rewrite_external_link, ctx), source)
    return BARE_URL.sub(partial(rewrite_bare_url, ctx), source)


def convert(
    text: str,
    *,
    resolve: Resolver,
    manpage_anchor: Callable[[str, str | None], str | None] | None = None,
    has_image: Callable[[str], bool] | None = None,
) -> Conversion:
    """Rewrite one wiki page's Markdown for use on this site."""
    metadata, body = split_metadata(text)
    result = Conversion(body='', metadata=metadata)
    ctx = _Rewrite(result, resolve, manpage_anchor, has_image)

    metadata.fields = {key: rewrite_all(ctx, value) for key, value in metadata.fields.items()}
    result.body = rewrite_all(ctx, body).strip() + '\n'
    return result


def load(path: Path) -> str:
    """Read a wiki page, replacing anything that is not valid UTF-8."""
    return path.read_text(encoding='utf-8', errors='replace')
