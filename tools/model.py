"""The records the build passes around.

Plain data: everything that reads or writes them lives in the modules that do
the work, so these stay free of behaviour and free of imports beyond the POD
tree they carry.
"""

from dataclasses import dataclass, field
from pathlib import Path

from tools.pod import Node


@dataclass
class Section:
    """A ``=head1`` of the configuration manpage."""

    title: str
    nodes: list[Node] = field(default_factory=list)


@dataclass
class ConfSection:
    """One ``=head2`` under ``=head1 PLUGIN OPTIONS``.

    Most describe a plugin. A few -- ``cURL Statistics`` -- describe options
    shared by several, and have no plugin page of their own.
    """

    title: str
    plugin: str | None
    nodes: list[Node] = field(default_factory=list)


@dataclass
class Upstream:  # pylint: disable=too-many-instance-attributes
    """Everything parsed out of the upstream checkouts that the build needs."""

    collectd: Path
    wiki: Path
    conf_tree: Node
    sections: list[Section]
    plugin_sections: dict[str, list[Node]]
    conf_sections: list[ConfSection]
    filter_items: dict[str, list[Node]]
    source_plugins: set[str]
    version_date: str
    wiki_date: str


@dataclass
class Plugin:
    """One plugin this site documents."""

    name: str
    kind: str  # read | write | filter | other
    wiki_page: str | None = None
    has_config: bool = False
    in_source: bool = True


def by_name(plugin: Plugin) -> str:
    """Sort key: plugins are listed case-insensitively by name."""
    return plugin.name.lower()
