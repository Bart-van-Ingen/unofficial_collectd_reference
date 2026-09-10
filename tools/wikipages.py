"""Wiki pages carried over as concepts, protocols and contributing sections."""

import shutil

from tools import (
    config,
    links,
)
from tools.output import write


def build_wiki_sections(index: links.LinkIndex) -> None:
    """Write the concepts, protocols and contributing sections."""
    titles = {
        'concepts': ('Concepts', 'How collectd models and moves metrics.'),
        'protocols': ('Protocols', 'The wire formats collectd speaks.'),
        'contributing': (
            'Contributing',
            'Working on collectd itself: internals, style and process.',
        ),
    }
    for section, entries in config.WIKI_SECTIONS.items():
        rows = []
        for stem, title in entries:
            conversion = links.read_wiki(index, stem)
            if conversion is None:
                print(f'  ! missing wiki page: {stem}')
                continue
            write(
                f'{section}/{stem.lower()}.md',
                f'# {title}\n\n{conversion.body}',
            )
            rows.append(f'- [{title}](/{section}/{stem.lower()}/)')

        heading, blurb = titles[section]
        write(
            f'{section}/index.md',
            '\n'.join([f'# {heading}', '', blurb, '', *rows]),
        )


def build_assets(index: links.LinkIndex) -> None:
    """Copy every referenced wiki image into ``docs/assets/wiki/``."""
    target = config.DOCS / 'assets' / 'wiki'
    target.mkdir(parents=True, exist_ok=True)
    missing = []
    for image in sorted(index.images):
        source = index.wiki_root / image
        if source.is_file():
            shutil.copy2(source, target / image)
        else:
            missing.append(image)
    print(f'  copied {len(index.images) - len(missing)} wiki images')
    if missing:
        print(f'  ! {len(missing)} referenced images missing from the wiki')
