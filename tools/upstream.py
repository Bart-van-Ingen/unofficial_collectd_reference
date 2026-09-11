"""Read the pinned collectd checkout into the records in :mod:`tools.model`."""

import re
from pathlib import Path

from tools import config
from tools.model import ConfSection, Section, Upstream
from tools.pod import Node, parse, render_inline
from tools.sources import repo_date, sync_all


#: ``(heading, item name) -> plugin``, inverted from the config once so matching
#: an item is a lookup rather than a scan of every entry.
_FILTER_BY_ITEM = {
    (item.heading, item.key): plugin for plugin, item in config.FILTER_ITEMS.items()
}

#: The manpage headings those items live under, derived from the same table so a
#: new heading only has to be added in one place.
_FILTER_HEADINGS = {owner for owner, _ in _FILTER_BY_ITEM}


#: A plugin's ``=head2``. Nearly all use the ``C<>`` form; ``Plugin Connectivity``
#: is written bare, and was silently dropped for as long as only the first was
#: matched -- taking the whole plugin with it.
PLUGIN_HEAD = re.compile(r'^Plugin\s+(?:C<(.+?)>|(\S+))$')

#: ``=head2`` sections under PLUGIN OPTIONS that document shared options rather
#: than a plugin. Anything else that fails to parse as a plugin is a mistake.
SHARED_SECTIONS = {'cURL Statistics'}


def read_pod(collectd: Path, name: str) -> str:
    """Read one ``.pod`` source out of the collectd checkout."""

    return (collectd / 'src' / f'{name}.pod').read_text(encoding='utf-8', errors='replace')


def split_sections(tree: Node) -> list[Section]:
    """Split a parsed manpage into its ``=head1`` chapters."""

    sections: list[Section] = []

    for node in tree.children:
        if node.kind == 'head' and node.level == 1:
            sections.append(Section(node.text))
        elif sections:
            sections[-1].nodes.append(node)

    return sections


def split_conf_sections(section: Section, known: set[str]) -> list[ConfSection]:
    """Split ``=head1 PLUGIN OPTIONS`` into its ``=head2`` sections, in order.

    *known* is the plugin list from ``configure.ac``; it decides the spelling of
    a name the manpage capitalises for prose ("Connectivity" -> "connectivity").
    """

    sections: list[ConfSection] = []

    for node in section.nodes:
        if node.kind != 'head' or node.level != 2:
            if sections:
                sections[-1].nodes.append(node)
            continue

        title = node.text.strip()

        if title in SHARED_SECTIONS:
            sections.append(ConfSection(title=title, plugin=None))
            continue

        match = PLUGIN_HEAD.match(title)

        if not match:
            raise ValueError(
                f'unrecognised =head2 under PLUGIN OPTIONS: {title!r}. Add it to '
                'SHARED_SECTIONS if it does not document a plugin.'
            )
        name = (match.group(1) or match.group(2)).strip()

        if name not in known and name.lower() in known:
            name = name.lower()
        sections.append(ConfSection(title=title, plugin=name))

    return sections


def split_filter_items(section: Section) -> dict[str, list[Node]]:
    """Pull each match/target out of the filter chapter's ``=item`` lists."""

    found: dict[str, list[Node]] = {}
    heading: str | None = None

    for node in section.nodes:
        if node.kind == 'head':
            heading = node.text.strip()
            continue

        if node.kind != 'list' or heading not in _FILTER_HEADINGS:
            continue

        for item in node.children:
            if item.kind != 'item':
                continue
            name = render_inline(item.text, plain=True).strip()

            if plugin := _FILTER_BY_ITEM.get((heading, name)):
                found[plugin] = item.children

    return found


def load_upstream(*, update: bool) -> Upstream:
    """Sync both repositories and parse everything the build needs from them."""

    paths = sync_all(update=update)
    collectd, wiki = paths['collectd'], paths['wiki']

    tree = parse(read_pod(collectd, 'collectd.conf'))
    sections = split_sections(tree)
    by_title = {section.title: section for section in sections}

    configure = (collectd / 'configure.ac').read_text(encoding='utf-8', errors='replace')
    source_plugins = {
        match.group(1)
        for match in re.finditer(r'^AC_PLUGIN\(\[([a-zA-Z0-9_]+)', configure, re.MULTILINE)
    }

    conf_sections = split_conf_sections(by_title['PLUGIN OPTIONS'], source_plugins)

    return Upstream(
        collectd=collectd,
        wiki=wiki,
        conf_tree=tree,
        sections=sections,
        plugin_sections={s.plugin: s.nodes for s in conf_sections if s.plugin},
        conf_sections=conf_sections,
        filter_items=split_filter_items(by_title['FILTER CONFIGURATION']),
        source_plugins=source_plugins,
        version_date=repo_date(collectd),
        wiki_date=repo_date(wiki),
    )
