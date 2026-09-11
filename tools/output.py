"""Where generated files go, and the small helpers that shape them."""

import re

from tools import config


#: Snippet fragments included by both the plugin pages and collectd.conf(5).
SNIPPETS = config.ROOT / 'snippets'


def slugify(text: str) -> str:
    """Match the anchor Python-Markdown's toc extension generates."""

    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[*_`\\]', '', text)
    text = re.sub(r'[^\w\s-]', '', text.lower()).strip()

    return re.sub(r'[-\s]+', '-', text)


def write(relative: str, text: str) -> None:
    """Write one generated page under ``docs/``."""

    path = config.DOCS / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n', encoding='utf-8')


def write_snippet(relative: str, text: str) -> None:
    """Write one shared configuration fragment under ``snippets/``."""

    path = SNIPPETS / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n', encoding='utf-8')


def cell(value: str) -> str:
    """Flatten an infobox value so it survives inside a table cell."""

    value = re.sub(r'\s*<br\s*/?>\s*', ', ', value)

    return ' '.join(value.split()).replace('|', '&#124;')
