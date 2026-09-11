"""Render a parsed POD document (see :mod:`tools.pod`) as Markdown."""

import re
from dataclasses import dataclass

from tools.pod import LinkResolver, Node, render_inline


INDENT = '    '

_BULLET = re.compile(r'^\*?$')
_NUMBERED = re.compile(r'^(\d+)[.)]?$')


@dataclass(frozen=True)
class Options:
    """How a POD tree should be rendered."""

    heading_offset: int = 0
    min_heading: int = 1
    link: LinkResolver | None = None


def fence_language(code: str) -> str:
    """Guess a highlighting language for a verbatim block."""

    if re.search(r'^\s*(<Plugin|<Chain|<Rule|<Match|<Target|LoadPlugin)\b', code, re.MULTILINE):
        return 'apacheconf'

    if re.search(r'^\s*(\$|#!)', code):
        return 'console'

    return 'text'


def indent_block(text: str, prefix: str = INDENT) -> str:
    """Indent every non-empty line of an already-rendered block."""

    return '\n'.join(prefix + line if line else '' for line in text.split('\n'))


def list_style(items: list[Node]) -> str:
    """Decide how a POD ``=over`` list should be rendered."""

    if all(_BULLET.match(item.text.strip()) for item in items):
        return 'bullet'

    if all(_NUMBERED.match(item.text.strip()) for item in items):
        return 'numbered'

    return 'definition'


def render_blocks(nodes: list[Node], opts: Options) -> list[str]:
    """Render each child node, dropping the ones that produce nothing."""

    return [rendered for node in nodes if (rendered := render_block(node, opts))]


def render_block(node: Node, opts: Options) -> str:
    """Render one node as a single Markdown block."""

    match node.kind:
        case 'head':
            level = max(opts.min_heading, min(6, node.level + opts.heading_offset))
            return f'{"#" * level} {render_inline(node.text, link=opts.link)}'

        case 'para':
            return render_inline(node.text, link=opts.link)

        case 'verbatim':
            return f'```{fence_language(node.text)}\n{node.text}\n```'

        case 'list':
            return render_list(node, opts)

        case _:
            return ''


def render_list(node: Node, opts: Options) -> str:
    """Render an ``=over`` list as a bullet, numbered or definition list."""

    items = [child for child in node.children if child.kind == 'item']

    if not items:
        return '\n\n'.join(render_blocks(node.children, opts))

    style = list_style(items)
    rendered: list[str] = []

    for position, item in enumerate(items, start=1):
        body = render_blocks(item.children, opts)

        if style == 'definition':
            term = render_inline(item.text, link=opts.link)
            # A definition list term must be a single line.
            term = ' '.join(term.split('\n'))

            if body:
                first, *rest = body
                chunks = [f':{INDENT[1:]}{indent_block(first)[len(INDENT) :]}']
                chunks += [indent_block(block) for block in rest]
                rendered.append(term + '\n' + '\n\n'.join(chunks))
            else:
                rendered.append(term + '\n:' + INDENT[1:])
            continue

        marker = '-' if style == 'bullet' else f'{position}.'
        marker = marker.ljust(len(INDENT))

        if body:
            first, *rest = body
            chunks = [marker + indent_block(first)[len(INDENT) :]]
            chunks += [indent_block(block) for block in rest]
            rendered.append('\n\n'.join(chunks))
        else:
            rendered.append(marker.rstrip())

    return '\n\n'.join(rendered)


def to_markdown(
    node: Node,
    *,
    heading_offset: int = 0,
    link: LinkResolver | None = None,
    min_heading: int = 1,
) -> str:
    """Render a POD tree as Markdown.

    ``heading_offset`` shifts every ``=headN`` down the hierarchy, so a fragment
    can be embedded under a heading the including page provides; ``min_heading``
    is the shallowest level it may end up at.
    """

    return '\n\n'.join(render_blocks(node.children, Options(heading_offset, min_heading, link)))
