"""Fragments the plugin pages and the filter pages both assemble.

Kept apart from :mod:`tools.output`, which knows only about files, because
these need to know how the site links to itself and how POD renders.
"""

from tools import links
from tools.output import cell, write_snippet
from tools.pod import Node
from tools.render import to_markdown
from tools.wiki import Conversion


#: Infobox rows shown on any page, when the wiki supplies them.
COMMON_FIELDS = (
    ('Status', 'status'),
    ('Since', 'firstversion'),
    ('Copyright', 'copyright'),
    ('License', 'license'),
)


def conf_window(snippet: str, *, source: str) -> str:
    """The embedded view onto one section of collectd.conf(5).

    The body is a snippet include, so this is a genuine window onto the
    manual page rather than a second copy of it. It ships collapsed: the
    option lists run long, and most readers want the prose first.
    """

    return (
        '<details class="manpage-window" markdown>\n'
        '<summary class="manpage-window__label">Configuration options '
        '&middot; from <code>collectd.conf(5)</code></summary>\n\n'
        f'<p class="manpage-window__source"><a href="{source}">'
        'See this section in the full configuration reference</a></p>\n\n'
        f'--8<-- "{snippet}"\n\n'
        '</details>'
    )


def infobox(
    name: str,
    conversion: Conversion | None,
    fields: tuple[tuple[str, str], ...],
    configuration: str,
) -> str:
    """The two-column table at the top of a plugin or filter page."""

    rows = [('Plugin name', f'`{name}`')]

    if conversion:
        for label, key in fields:
            if value := conversion.metadata.get(key):
                rows.append((label, cell(value)))
    rows.append(('Configuration', configuration))
    body = '\n'.join(f'| {label} | {value} |' for label, value in rows)

    return f'| | |\n|---|---|\n{body}'


def configuration_window(
    snippet: str, nodes: list[Node], *, anchor: str, heading_offset: int
) -> str:
    """Write one shared configuration fragment and return the window onto it."""

    write_snippet(
        snippet,
        to_markdown(
            Node('root', children=nodes),
            heading_offset=heading_offset,
            min_heading=3,
            link=links.pod_link,
        ),
    )

    return conf_window(snippet, source=anchor)
