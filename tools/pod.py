"""Parse Perl POD (the source form of collectd's manpages) into Markdown.

collectd's manpages live in ``src/*.pod`` in the collectd repository. They are
the authoritative description of every configuration option, so this site
renders them directly rather than keeping a hand-written copy that would drift.

The parser is deliberately small: it only implements the POD subset collectd
actually uses (surveyed across all 16 ``.pod`` files), and raises on anything
unexpected instead of silently dropping content.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field


_IGNORED_COMMANDS = {'cut', 'pod', 'encoding', 'for', 'begin', 'end'}

_ENTITIES = {
    'lt': '<',
    'gt': '>',
    'sol': '/',
    'verbar': '|',
    'nbsp': '\N{NO-BREAK SPACE}',
    'amp': '&',
    'quot': '"',
}

# Only the characters Python-Markdown would otherwise interpret as markup.
_ESCAPE = re.compile(r'([\\`*_\[\]|])')

_CODE_START = re.compile(r'(?<![A-Za-z0-9])([A-Z])<')

# Resolves L<...> targets to a URL; set by the site builder.
LinkResolver = Callable[[str], str | None]


# --- document model ---------------------------------------------------------


@dataclass
class Node:
    """One node of a parsed POD document."""

    kind: str  # root | head | para | verbatim | list | item
    level: int = 0  # head: 1-4;  list: the N of "=over N"
    text: str = ''
    children: list[Node] = field(default_factory=list)


# --- paragraph splitting ----------------------------------------------------


def paragraphs(pod: str) -> Iterable[list[str]]:
    """Yield POD paragraphs (runs of non-blank lines)."""
    current: list[str] = []
    for line in pod.expandtabs(8).splitlines():
        if line.strip():
            current.append(line)
        elif current:
            yield current
            current = []
    if current:
        yield current


def dedent(lines: list[str]) -> str:
    """Strip the common leading indentation from a verbatim block."""
    indent = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
    return '\n'.join(line[indent:] if line.strip() else '' for line in lines)


# --- parsing ----------------------------------------------------------------


# One branch per POD command; collapsing them would hide the grammar.
def parse(pod: str) -> Node:  # pylint: disable=too-many-branches,too-complex
    """Parse a POD document into a tree of :class:`Node`."""
    root = Node('root')
    stack: list[Node] = [root]

    for para in paragraphs(pod):
        first = para[0]

        if first.startswith('='):
            command, _, rest = first.partition(' ')
            command = command[1:]
            argument = ' '.join([rest.strip()] + [line.strip() for line in para[1:]]).strip()

            match command:
                case 'over':
                    node = Node('list', level=int(argument or 4))
                    stack[-1].children.append(node)
                    stack.append(node)
                case 'back':
                    while len(stack) > 1:
                        if stack.pop().kind == 'list':
                            break
                case 'item':
                    if stack[-1].kind == 'item':
                        stack.pop()
                    if stack[-1].kind != 'list':  # stray =item, synthesise a list
                        node = Node('list', level=4)
                        stack[-1].children.append(node)
                        stack.append(node)
                    item = Node('item', text=argument)
                    stack[-1].children.append(item)
                    stack.append(item)
                case _ if command.startswith('head'):
                    del stack[1:]  # a =head always closes back to the root
                    root.children.append(Node('head', level=int(command[4:] or 1), text=argument))
                case _ if command in _IGNORED_COMMANDS:
                    continue
                case _:
                    raise ValueError(f'unsupported POD command: ={command}')

        elif first[:1].isspace():
            body = dedent(para)
            previous = stack[-1].children[-1] if stack[-1].children else None
            if previous is not None and previous.kind == 'verbatim':
                previous.text += '\n\n' + body  # blank line inside a code block
            else:
                stack[-1].children.append(Node('verbatim', text=body))

        else:
            stack[-1].children.append(Node('para', text=' '.join(line.strip() for line in para)))

    return root


# --- inline formatting codes ------------------------------------------------


def escape(text: str) -> str:
    """Escape text so Markdown renders it literally."""
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return _ESCAPE.sub(r'\\\1', text)


def code_span(text: str) -> str:
    """Wrap text in a Markdown code span, widening the fence as needed."""
    if not text:
        return ''
    ticks = '`'
    while ticks in text:
        ticks += '`'
    pad = ' ' if text.startswith('`') or text.endswith('`') else ''
    return f'{ticks}{pad}{text}{pad}{ticks}'


def matching_angle(text: str, start: int) -> int:
    """Index of the ``>`` closing the code opened just before *start*."""
    depth = 1
    for i in range(start, len(text)):
        char = text[i]
        if char == '<' and i and text[i - 1].isupper() and (i < 2 or not text[i - 2].isalnum()):
            depth += 1
        elif char == '>':
            depth -= 1
            if depth == 0:
                return i
    return -1


# One branch per POD formatting code; collapsing them would hide the grammar.
def render_inline(  # pylint: disable=too-complex
    text: str, *, plain: bool = False, link: LinkResolver | None = None
) -> str:
    """Render POD inline formatting codes to Markdown.

    With ``plain=True`` the result is unescaped literal text, used for the
    inside of code spans and for anything that must not contain markup.
    """
    out: list[str] = []
    position = 0

    while position < len(text):
        match = _CODE_START.search(text, position)

        if not match:
            chunk = text[position:]
            out.append(chunk if plain else escape(chunk))
            break

        chunk = text[position : match.start()]
        out.append(chunk if plain else escape(chunk))

        letter = match.group(1)
        close = matching_angle(text, match.end())

        if close < 0:  # unbalanced: treat as literal
            out.append(escape(match.group(0)) if not plain else match.group(0))
            position = match.end()
            continue

        inner = text[match.end() : close]
        position = close + 1

        match letter:
            case 'E':
                entity = _ENTITIES.get(inner)
                if entity is None and inner.isdigit():
                    entity = chr(int(inner))
                entity = entity if entity is not None else inner
                out.append(entity if plain else escape(entity))
            case 'X' | 'Z':  # index entry / zero-width: no output
                continue
            case 'C' | 'F':
                literal = render_inline(inner, plain=True, link=link)
                out.append(literal if plain else code_span(literal))
            case 'B':
                body = render_inline(inner, plain=plain, link=link)
                out.append(body if plain else f'**{body}**')
            case 'I':
                body = render_inline(inner, plain=plain, link=link)
                out.append(body if plain else f'*{body}*')
            case 'S':
                body = render_inline(inner, plain=plain, link=link)
                out.append(body.replace(' ', '\N{NO-BREAK SPACE}'))
            case 'L':
                out.append(render_link(inner, plain=plain, link=link))
            case _:
                out.append(render_inline(inner, plain=plain, link=link))

    return ''.join(out)


def render_link(target: str, *, plain: bool, link: LinkResolver | None) -> str:
    """Render one ``L<>`` link, degrading to a code span when it cannot resolve."""
    label, _, destination = target.partition('|')
    if not destination:
        label, destination = '', target

    url = link(destination) if link else None
    text = label or destination.replace('"', '')

    if plain or url is None:
        rendered = render_inline(text, plain=True, link=link)
        return rendered if plain else code_span(rendered)
    return f'[{render_inline(text, plain=False, link=link)}]({url})'
