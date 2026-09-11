"""Rewrite the generated parts of ``zensical.toml``: the nav and the site URL."""

import re

from tools import (
    config,
    links,
)
from tools.model import Plugin, by_name


SITE_URL_LINE = re.compile(r'^site_url = .*$', re.MULTILINE)


def nav_entry(title: str, target: str, indent: int) -> str:
    """One ``{ "Title" = "path" }`` line of the generated nav."""

    pad = '  ' * indent

    return f'{pad}{{ "{title}" = "{target}" }},'


def nav_group(title: str, children: list[str], indent: int) -> list[str]:
    """One nav section wrapping *children* under a heading."""

    pad = '  ' * indent

    return [f'{pad}{{ "{title}" = [', *children, f'{pad}] }},']


def build_nav(plugins: dict[str, Plugin]) -> None:  # pylint: disable=too-many-locals
    """Rewrite the generated region of ``zensical.toml``."""

    lines: list[str] = ['nav = [', nav_entry('Home', 'index.md', 1)]

    for section, heading in (
        ('concepts', 'Concepts'),
        ('protocols', 'Protocols'),
    ):
        children = [nav_entry('Overview', f'{section}/index.md', 2)]
        children += [
            nav_entry(title, f'{section}/{stem.lower()}.md', 2)
            for stem, title in config.WIKI_SECTIONS[section]
            if (config.DOCS / section / f'{stem.lower()}.md').is_file()
        ]
        lines += nav_group(heading, children, 1)

    plugin_children = [nav_entry('All plugins', 'plugins/index.md', 2)]
    plugin_children += [
        nav_entry(plugin.name, f'plugins/{plugin.name.lower()}.md', 2)
        for plugin in sorted(plugins.values(), key=by_name)
    ]
    lines += nav_group('Plugins', plugin_children, 1)

    filter_children = [nav_entry('Overview', 'filters/index.md', 2)]
    filter_children += [
        nav_entry(links.filter_title(name), f'filters/{name}.md', 2)
        for name in links.filter_names()
    ]
    lines += nav_group('Filter chains', filter_children, 1)

    manpage_children = [nav_entry('All manual pages', 'manpages/index.md', 2)]
    manpage_children += [
        nav_entry(f'{name}({section})', f'manpages/{name}.md', 2)
        for name, section, _ in config.MANPAGES
    ]
    lines += nav_group('Manual pages', manpage_children, 1)

    contributing = [nav_entry('Overview', 'contributing/index.md', 2)]
    contributing += [
        nav_entry(title, f'contributing/{stem.lower()}.md', 2)
        for stem, title in config.WIKI_SECTIONS['contributing']
        if (config.DOCS / 'contributing' / f'{stem.lower()}.md').is_file()
    ]
    lines += nav_group('Contributing', contributing, 1)

    about = [
        nav_entry('About this site', 'about/index.md', 2),
        nav_entry('Link report', 'about/link-report.md', 2),
    ]
    lines += nav_group('About', about, 1)
    lines.append(']')

    path = config.ROOT / 'zensical.toml'
    text = SITE_URL_LINE.sub(f'site_url = "{config.SITE_URL}"', path.read_text(encoding='utf-8'))
    begin, end = '# BEGIN GENERATED NAV', '# END GENERATED NAV'
    pattern = re.compile(re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
    replacement = begin + '\n' + '\n'.join(lines) + '\n' + end
    match = pattern.search(text)

    if match is None:
        raise SystemExit('zensical.toml is missing the generated nav markers')
    path.write_text(text[: match.start()] + replacement + text[match.end() :], encoding='utf-8')
    print(f'  nav: {len(plugins)} plugins, {len(config.MANPAGES)} manpages')
