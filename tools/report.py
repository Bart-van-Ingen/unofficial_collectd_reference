"""The generated report of every wiki reference that could not be linked."""

import re
from operator import itemgetter
from pathlib import Path

from tools import (
    config,
    links,
)
from tools.output import slugify, write


def classify_target(wiki_root: Path, target: str) -> str:
    """Why a wiki reference could not be turned into a link."""
    if target.startswith('image: '):
        return 'missing image'
    if target.startswith(('http://', 'https://')):
        return 'retired collectd.org URL'
    if target in config.WIKI_EXCLUDE_PAGES:
        return 'excluded from this site'
    if any(re.search(pattern, target) for pattern in config.WIKI_EXCLUDE_PATTERNS):
        return 'excluded from this site'
    if (wiki_root / f'{target}.md').is_file():
        return 'wiki page not carried over'
    return 'missing from the wiki'


def build_link_report(index: links.LinkIndex) -> None:
    """Write the report of every wiki reference that could not be linked."""
    buckets: dict[str, dict[str, set[str]]] = {}
    for stem, targets in index.unresolved.items():
        for target in targets:
            buckets.setdefault(classify_target(index.wiki_root, target), {}).setdefault(
                target, set()
            ).add(stem)

    explanations = {
        'excluded from this site': (
            'Links to meeting minutes, per-release notes and pages about plugins '
            'that no longer ship. These were deliberately left out, so the links '
            'are rendered as plain text.'
        ),
        'wiki page not carried over': (
            'The wiki page exists but is not part of this site -- mostly '
            'third-party front-ends and companion projects.'
        ),
        'missing from the wiki': (
            'Genuinely broken on the wiki itself: the link points at a page that '
            'was never created or has since been deleted. Worth fixing upstream.'
        ),
        'missing image': (
            'The page embeds an image that is not in the wiki repository. The '
            'image reference is dropped rather than left as a broken image.'
        ),
        'retired collectd.org URL': (
            'Points into the old collectd.org wiki or manual pages and could not '
            'be remapped onto a page here.'
        ),
    }

    # Both figures below come from `counts`, so the summary and the table can
    # never disagree: one reference is one (target, page) pair.
    counts = {
        cause: sum(len(pages) for pages in targets.values()) for cause, targets in buckets.items()
    }
    total = sum(counts.values())
    lines = [
        '# Link report',
        '',
        (
            'The collectd wiki links to a great deal that no longer resolves. The build '
            'rewrites every reference it can -- old `collectd.org/wiki/` URLs and old '
            'manual-page anchors are remapped onto this site -- and turns the rest into '
            'plain text, so no page here links somewhere broken.'
        ),
        '',
        (
            f'This is what was dropped: **{total} references across '
            f'{len(index.unresolved)} pages**, grouped by cause. The last two groups are '
            'the ones worth fixing upstream.'
        ),
        '',
        '| Cause | References |',
        '|---|---|',
    ]
    counts = {cause: sum(len(v) for v in targets.values()) for cause, targets in buckets.items()}
    order = [cause for cause, _ in sorted(counts.items(), key=itemgetter(1), reverse=True)]
    for cause in order:
        lines.append(f'| [{cause}](#{slugify(cause)}) | {counts[cause]} |')
    lines.append('')

    for cause in order:
        lines += [
            f'## {cause}',
            '',
            explanations[cause],
            '',
            '| Target | Linked from |',
            '|---|---|',
        ]
        for target in sorted(buckets[cause]):
            pages = sorted(buckets[cause][target])
            shown = ', '.join(pages[:4]) + (f' +{len(pages) - 4} more' if len(pages) > 4 else '')
            lines.append(f'| `{target}` | {shown} |')
        lines.append('')

    write('about/link-report.md', '\n'.join(lines))
