"""The plugin reference: one page per plugin, plus the index."""

import re

from tools import (
    config,
    links,
    wiki as wikimod,
)
from tools.model import Plugin, Upstream, by_name
from tools.output import slugify, write
from tools.page import COMMON_FIELDS, configuration_window, infobox
from tools.pod import render_inline


#: Infobox rows a plugin page shows, when the wiki supplies them.
PLUGIN_FIELDS = (('Type', 'type'), ('Callbacks', 'callbacks'), *COMMON_FIELDS)


def collect_plugins(up: Upstream) -> dict[str, Plugin]:
    """Every plugin the site documents, keyed by its manpage spelling."""
    plugins: dict[str, Plugin] = {}
    wiki_by_plugin: dict[str, str] = {}
    for path in sorted(up.wiki.glob('Plugin-*.md')):
        if path.stem in config.WIKI_EXCLUDE_PAGES or path.stem in config.WIKI_COMPANIONS:
            continue
        if any(re.search(p, path.stem) for p in config.WIKI_EXCLUDE_PATTERNS):
            continue
        wiki_by_plugin.setdefault(links.wiki_plugin_name(path.stem), path.stem)

    names = set(up.plugin_sections) | set(config.CONFIGLESS_PLUGINS)
    for name in sorted(names, key=str.lower):
        if name.startswith(config.FILTER_PLUGIN_PREFIXES):
            continue
        plugins[name] = Plugin(
            name=name,
            kind=plugin_kind(name),
            wiki_page=wiki_by_plugin.get(name.lower()) or wiki_by_plugin.get(name),
            has_config=name in up.plugin_sections,
            in_source=name in up.source_plugins,
        )

    return plugins


def plugin_kind(name: str) -> str:
    """Which part of the daemon a plugin belongs to: read, write or filter."""
    if name.startswith('write_') or name in {
        'amqp',
        'amqp1',
        'csv',
        'rrdtool',
        'rrdcached',
        'network',
        'unixsock',
        'riemann',
        'mqtt',
        'kafka',
    }:
        return 'write'
    if name.startswith(('notify_', 'match_', 'target_')):
        return 'filter'
    return 'read'


def metadata_table(conversion: wikimod.Conversion | None, plugin: Plugin) -> str:
    """The infobox at the top of a plugin page."""
    configuration = (
        f'[collectd.conf(5)]({links.manpage_url("collectd.conf")}#plugin-{slugify(plugin.name)})'
        if plugin.has_config
        else 'none'
    )
    return infobox(plugin.name, conversion, PLUGIN_FIELDS, configuration)


def plugin_summary(up: Upstream, plugin: Plugin, conversion: wikimod.Conversion | None) -> str:
    """A lead paragraph for a plugin page, or empty when its body already opens with prose."""
    if conversion:
        for paragraph in conversion.body.split('\n\n'):
            text = paragraph.strip()
            if text and not text.startswith(('#', '|', '!', '<', '-', '*')):
                return ''
    if plugin.has_config:
        for node in up.plugin_sections[plugin.name]:
            if node.kind == 'para':
                return render_inline(node.text, link=links.pod_link)
    return ''


def build_plugin_pages(up: Upstream, plugins: dict[str, Plugin], index: links.LinkIndex) -> None:
    """Write one page per plugin, along with its configuration snippet."""
    for plugin in plugins.values():
        conversion = links.read_wiki(index, plugin.wiki_page) if plugin.wiki_page else None
        parts = [f'# {plugin.name} plugin', '']

        if summary := plugin_summary(up, plugin, conversion):
            parts += [summary, '']
        parts += [metadata_table(conversion, plugin), '']

        if conversion:
            parts += [conversion.body, '']
        elif not plugin.has_config:
            parts += ['This plugin is not documented further upstream.', '']

        for stem, entry in config.WIKI_COMPANIONS.items():
            if entry.owner != plugin.name:
                continue
            if companion := links.read_wiki(index, stem):
                parts += [f'## {entry.heading}', '', companion.body, '']

        parts += ['## Configuration', '']
        if plugin.has_config:
            anchor = f'{links.manpage_url("collectd.conf")}#plugin-{slugify(plugin.name)}'
            window = configuration_window(
                f'conf/{plugin.name.lower()}.md',
                up.plugin_sections[plugin.name],
                anchor=anchor,
                heading_offset=0,
            )
            parts += [window, '']
        else:
            parts += [
                'This plugin has no configuration options. Enable it with:',
                '',
                f'```apacheconf\nLoadPlugin {plugin.name}\n```',
                '',
            ]

        write(f'plugins/{plugin.name.lower()}.md', '\n'.join(parts))


def build_plugin_index(plugins: dict[str, Plugin]) -> None:
    """Write the table listing every plugin."""
    rows = []
    for plugin in sorted(plugins.values(), key=by_name):
        configurable = 'yes' if plugin.has_config else '—'
        docs = (
            'wiki + manpage'
            if plugin.wiki_page and plugin.has_config
            else ('wiki' if plugin.wiki_page else 'manpage')
        )
        rows.append(
            f'| [`{plugin.name}`](/plugins/{plugin.name.lower()}/) '
            f'| {plugin.kind} | {configurable} | {docs} |'
        )
    total = len(plugins)
    configured = sum(1 for p in plugins.values() if p.has_config)
    write(
        'plugins/index.md',
        '\n'.join(
            [
                '# Plugins',
                '',
                (
                    f'collectd {config.VERSION} ships {total} plugins. {configured} of them take '
                    'configuration; the rest are enabled with a bare `LoadPlugin` line.'
                ),
                '',
                (
                    "Every plugin page embeds that plugin's section of "
                    f'[collectd.conf(5)]({links.manpage_url("collectd.conf")}) directly, '
                    'so the options you read here are the options the daemon actually parses.'
                ),
                '',
                '| Plugin | Kind | Configurable | Sources |',
                '|---|---|---|---|',
                *rows,
            ]
        ),
    )
