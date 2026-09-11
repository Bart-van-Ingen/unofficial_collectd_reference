"""Generate the documentation site from the pinned upstream sources.

Nothing under ``docs/`` or ``snippets/`` is written by hand: this package builds
both from the collectd repository and the collectd wiki. Run it with

    uv run collectd-docs

Configuration reference text lives in exactly one place -- ``snippets/conf/``,
extracted from ``src/collectd.conf.pod`` -- and is included both by the plugin
page and by the full ``collectd.conf(5)`` page, so the two can never disagree.
"""

import argparse
import shutil

from tools import config
from tools.filters import build_filter_pages
from tools.links import build_index
from tools.manpages import build_manpages
from tools.model import Plugin, Upstream
from tools.nav import build_nav
from tools.output import SNIPPETS, write
from tools.plugins import build_plugin_index, build_plugin_pages, collect_plugins
from tools.report import build_link_report
from tools.upstream import load_upstream
from tools.wikipages import build_assets, build_wiki_sections


def build_content(up: Upstream, plugins: dict[str, Plugin]) -> None:
    """Copy the hand-written pages in ``content/`` over the generated tree."""

    for source in sorted(config.CONTENT.rglob('*.md')):
        relative = source.relative_to(config.CONTENT)
        text = source.read_text(encoding='utf-8')
        text = text.replace('{{ version }}', config.VERSION)
        text = text.replace('{{ plugin_count }}', str(len(plugins)))
        text = text.replace('{{ wiki_date }}', up.wiki_date)
        text = text.replace('{{ release_date }}', up.version_date)
        write(str(relative), text)


def main() -> None:
    """Build the whole site from the pinned upstream sources."""

    parser = argparse.ArgumentParser(
        description='Generate the collectd documentation site from the pinned sources.'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='fetch upstream changes before building',
    )
    args = parser.parse_args()

    up = load_upstream(update=args.update)

    if config.DOCS.exists():
        shutil.rmtree(config.DOCS)

    if SNIPPETS.exists():
        shutil.rmtree(SNIPPETS)

    print('Building pages')
    plugins = collect_plugins(up)
    index = build_index(up.wiki, plugins)

    build_plugin_pages(up, plugins, index)
    build_plugin_index(plugins)
    build_filter_pages(up, index)
    build_manpages(up, plugins)
    build_wiki_sections(index)
    build_assets(index)
    build_link_report(index)
    build_content(up, plugins)
    build_nav(plugins)

    pages = sum(1 for _ in config.DOCS.rglob('*.md'))
    snippets = sum(1 for _ in SNIPPETS.rglob('*.md'))
    print(f'  wrote {pages} pages and {snippets} snippets')


if __name__ == '__main__':
    main()
