"""The manual pages, rendered from the ``.pod`` sources."""

from tools import (
    config,
    links,
)
from tools.model import Plugin, Upstream
from tools.output import write
from tools.pod import Node, parse
from tools.render import to_markdown
from tools.upstream import read_pod


def build_manpages(up: Upstream, plugins: dict[str, Plugin]) -> None:
    """Write every manual page, plus the index that lists them."""
    for name, section, blurb in config.MANPAGES:
        if name == 'collectd.conf':
            build_conf_manpage(up, plugins, section, blurb)
            continue
        tree = parse(read_pod(up.collectd, name))
        body = to_markdown(tree, heading_offset=1, min_heading=2, link=links.pod_link)
        write(
            f'manpages/{name}.md',
            f'# {name}({section})\n\n*{blurb}.* Generated from '
            f'`src/{name}.pod` in collectd {config.VERSION}.\n\n{body}',
        )

    rows = [
        f'| [{name}({section})]({links.manpage_url(name)}) | {blurb} |'
        for name, section, blurb in config.MANPAGES
    ]
    write(
        'manpages/index.md',
        '\n'.join(
            [
                '# Manual pages',
                '',
                (
                    f'The manual pages shipped with collectd {config.VERSION}, rendered from the '
                    '`.pod` sources in the collectd repository.'
                ),
                '',
                '| Page | Covers |',
                '|---|---|',
                *rows,
            ]
        ),
    )


def build_conf_manpage(up: Upstream, plugins: dict[str, Plugin], section: int, blurb: str) -> None:
    """Reassemble collectd.conf(5), with each plugin section as a snippet.

    The plugin sections are the same files the plugin pages include, and
    each one is introduced by a link to the plugin page, so a reader who
    lands in the configuration reference can get to the prose.
    """
    parts = [
        f'# collectd.conf({section})',
        '',
        f'*{blurb}.* Generated from `src/collectd.conf.pod` in collectd {config.VERSION}.',
        '',
        (
            "Every `Plugin` block below is also shown on that plugin's own page, "
            'alongside the description, dependencies and examples.'
        ),
        '',
    ]

    for chapter in up.sections:
        if chapter.title in {'NAME', 'AUTHOR'}:
            continue
        parts += [f'## {chapter.title.title()}', '']

        if chapter.title == 'PLUGIN OPTIONS':
            parts += [
                (
                    'One section per plugin, in the order the manpage lists them. '
                    f'See the [plugin index](/plugins/) for all '
                    f'{len(plugins)} plugins including those that take no '
                    'configuration.'
                ),
                '',
            ]
            for conf in up.conf_sections:
                if conf.plugin is None:
                    # Shared options several plugins refer back to; no page of
                    # their own, so they are rendered inline, in document order.
                    parts += [
                        f'### {conf.title}',
                        '',
                        to_markdown(
                            Node('root', children=conf.nodes),
                            heading_offset=2,
                            min_heading=4,
                            link=links.pod_link,
                        ),
                        '',
                    ]
                    continue

                name = conf.plugin
                parts += [f'### Plugin {name}', '']
                if name in plugins:
                    parts += [
                        (
                            f'[Full documentation for the {name} plugin →]'
                            f'({links.plugin_url(name)}){{ .manpage-window__link }}'
                        ),
                        '',
                    ]
                parts += [f'--8<-- "conf/{name.lower()}.md"', '']
            continue

        body = to_markdown(
            Node('root', children=chapter.nodes),
            heading_offset=2,
            min_heading=3,
            link=links.pod_link,
        )
        parts += [body, '']

    write('manpages/collectd.conf.md', '\n'.join(parts))
