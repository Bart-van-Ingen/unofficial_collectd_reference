"""The site's URL namespace.

Which page every plugin, filter, manual page and wiki stem lives at, and how a
POD or wiki reference resolves into it. The URL helpers are pure; the ones that
need to know what exists take a :class:`LinkIndex`, which also collects the
images and the dead references the build reports on afterwards.
"""

import re
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

from tools import (
    config,
    wiki as wikimod,
)
from tools.model import Plugin
from tools.output import slugify


@dataclass
class LinkIndex:
    """What the site contains, plus what could not be linked to."""

    wiki_root: Path
    plugins: dict[str, Plugin] = field(default_factory=dict)
    pages: dict[str, str] = field(default_factory=dict)  # wiki stem -> site url
    images: set[str] = field(default_factory=set)
    unresolved: dict[str, list[str]] = field(default_factory=dict)


# --- naming: pure, no index needed ------------------------------------------


def wiki_plugin_name(stem: str) -> str:
    """The plugin that a wiki page stem describes."""

    if stem in config.WIKI_PLUGIN_ALIASES:
        return config.WIKI_PLUGIN_ALIASES[stem]

    return stem[len('Plugin-') :].lower().replace('-', '_')


def site_path(path: str) -> str:
    """A root-relative *path*, prefixed with the base path the site is served under."""

    return f'{config.BASE_PATH}{path}'


def plugin_url(name: str) -> str:
    """The site URL of a plugin's page."""

    return site_path(f'/plugins/{name.lower()}/')


def filter_url(name: str) -> str:
    """The site URL of a match or target's page."""

    return site_path(f'/filters/{name}/')


def manpage_url(name: str, anchor: str | None = None) -> str:
    """The site URL of a manual page, optionally at one of its anchors."""

    url = site_path(f'/manpages/{name}/')

    return f'{url}#{anchor}' if anchor else url


def pod_link(target: str) -> str | None:  # pylint: disable=too-many-return-statements
    """Resolve a POD ``L<>`` target to a site URL, or ``None`` if it is not one."""

    target = target.strip()

    if match := re.fullmatch(r'([a-z0-9.\-_]+)\((\d)\)', target):
        name = match.group(1)

        if any(name == manpage for manpage, _, _ in config.MANPAGES):
            return manpage_url(name)
        return None

    if match := re.fullmatch(r'([a-z0-9.\-_]+)\(\d\)/"?(.+?)"?', target):
        name = match.group(1)

        if any(name == manpage for manpage, _, _ in config.MANPAGES):
            return manpage_url(name, slugify(match.group(2)))
        return None

    if target.startswith('/'):
        return f'#{slugify(target.lstrip("/").strip(chr(34)))}'

    if target.startswith('"') and target.endswith('"'):
        return f'#{slugify(target.strip(chr(34)))}'

    if target.startswith(('http://', 'https://', 'mailto:')):
        return target

    return None


def filter_names() -> list[str]:
    """Every match and target, in the order the site lists them."""

    return list(config.FILTER_ITEMS) + list(config.FILTER_EXTRA)


def filter_title(name: str) -> str:
    """The display title of a match or target. The two tables are total together."""

    if item := config.FILTER_ITEMS.get(name):
        return item.title

    return config.FILTER_EXTRA[name]


# --- resolution against the index -------------------------------------------


def build_index(wiki_root: Path, plugins: dict[str, Plugin]) -> LinkIndex:
    """Index every page a wiki reference is allowed to resolve to."""

    index = LinkIndex(wiki_root=wiki_root, plugins=plugins)

    for name in index.plugins:
        index.pages[f'Plugin-{name}'] = plugin_url(name)

    for stem, plugin in ((p.wiki_page, p) for p in index.plugins.values()):
        if stem:
            index.pages[stem] = plugin_url(plugin.name)

    for stem, entry in config.WIKI_COMPANIONS.items():
        if entry.owner in index.plugins:
            index.pages[stem] = plugin_url(entry.owner)

    for stem, plugin in config.WIKI_FILTER_PAGES.items():
        index.pages[stem] = filter_url(plugin)

    for section, entries in config.WIKI_SECTIONS.items():
        for stem, _ in entries:
            index.pages[stem] = site_path(f'/{section}/{stem.lower()}/')
    index.pages['Table-of-Plugins'] = site_path('/plugins/')
    index.pages['Table-of-Matches'] = site_path('/filters/')
    index.pages['List-of-manual-pages'] = site_path('/manpages/')
    index.pages['Chains'] = site_path('/filters/')

    return index


def resolve_wiki(index: LinkIndex, stem: str) -> str | None:
    """Resolve a wiki page stem to a site URL, or ``None`` if it was not carried over."""

    if stem in index.pages:
        return index.pages[stem]

    if stem.startswith('Plugin-'):
        name = wiki_plugin_name(stem)

        for candidate in index.plugins:
            if candidate.lower() == name:
                return plugin_url(candidate)

    return None


def manpage_anchor(index: LinkIndex, page: str, anchor: str | None) -> str | None:
    """Resolve an old manual-page anchor, preferring a plugin page where one exists."""

    if not any(page == manpage for manpage, _, _ in config.MANPAGES):
        return None

    if anchor and anchor.startswith('plugin_'):
        name = anchor[len('plugin_') :]

        for candidate in index.plugins:
            if candidate.lower() == name.lower():
                return plugin_url(candidate)

    return manpage_url(page, anchor)


def wiki_image_exists(wiki_root: Path, name: str) -> bool:
    """Whether an image the wiki references is actually present in the repository."""
    return (wiki_root / name).is_file()


def read_wiki(index: LinkIndex, stem: str) -> wikimod.Conversion | None:
    """Convert one wiki page, recording its images and its dead references."""

    path = index.wiki_root / f'{stem}.md'

    if not path.is_file():
        return None
    result = wikimod.convert(
        wikimod.load(path),
        resolve=partial(resolve_wiki, index),
        manpage_anchor=partial(manpage_anchor, index),
        has_image=partial(wiki_image_exists, index.wiki_root),
    )
    index.images |= result.images

    if result.unresolved:
        index.unresolved[stem] = result.unresolved

    return result
