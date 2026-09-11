"""The filter-chain reference: matches and targets."""

from tools import (
    config,
    links,
    wiki as wikimod,
)
from tools.model import Upstream
from tools.output import write
from tools.page import COMMON_FIELDS, configuration_window, infobox


#: Infobox rows a filter page shows, when the wiki supplies them.
FILTER_FIELDS = COMMON_FIELDS


def filter_metadata(up: Upstream, name: str, conversion: wikimod.Conversion | None) -> str:
    """The infobox at the top of a match or target page."""

    configuration = (
        f'[collectd.conf(5)]({links.manpage_url("collectd.conf")}#filter-configuration)'
        if name in up.filter_items
        else 'none'
    )

    return infobox(name, conversion, FILTER_FIELDS, configuration)


def build_filter_pages(up: Upstream, index: links.LinkIndex) -> None:
    """Write one page per match and target, plus the filter-chain overview."""

    names = links.filter_names()
    wiki_by_plugin = {v: k for k, v in config.WIKI_FILTER_PAGES.items()}

    for name in names:
        title = links.filter_title(name)
        parts = [f'# {title}', '']

        conversion = None

        if stem := wiki_by_plugin.get(name):
            conversion = links.read_wiki(index, stem)
        parts += [filter_metadata(up, name, conversion), '']

        if conversion:
            parts += [conversion.body, '']

        for stem, entry in config.WIKI_FILTER_COMPANIONS.items():
            if entry.owner == name and (companion := links.read_wiki(index, stem)):
                parts += [f'## {entry.heading}', '', companion.body, '']

        parts += ['## Configuration', '']
        if name in up.filter_items:
            window = configuration_window(
                f'conf/{name}.md',
                up.filter_items[name],
                anchor=f'{links.manpage_url("collectd.conf")}#filter-configuration',
                heading_offset=1,
            )
            parts += [window, '']
        else:
            parts += [
                (
                    'This is a built-in target and takes no configuration of its own. '
                    f'See [filter chains]({links.manpage_url("collectd.conf")}'
                    '#filter-configuration).'
                ),
                '',
            ]

        write(f'filters/{name}.md', '\n'.join(parts))

    overview = links.read_wiki(index, 'Chains')
    rows = [
        f'| [`{name}`]({links.filter_url(name)}) | '
        f'{"match" if name.startswith("match_") else "target"} |'
        for name in names
    ]
    write(
        'filters/index.md',
        '\n'.join(
            [
                '# Filter chains',
                '',
                (
                    'Filter chains let you drop, rewrite, duplicate and route metrics as they '
                    'pass through the daemon, before or after the cache.'
                ),
                '',
                (overview.body if overview else ''),
                '',
                '## Available matches and targets',
                '',
                '| Plugin | Kind |',
                '|---|---|',
                *rows,
            ]
        ),
    )
