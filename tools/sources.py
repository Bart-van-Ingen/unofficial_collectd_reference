"""Fetch the upstream collectd sources this site is generated from.

Both repositories are cloned into ``.cache/`` (git-ignored). The collectd
checkout is pinned to the release tag in :mod:`tools.config`; the wiki has no
tags, so it tracks its default branch -- which means it is checked out through
its remote-tracking ref, since ``git fetch`` never moves a local branch.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.config import CACHE, SOURCES


def run_git(*args: str, cwd: Path | None = None) -> str:
    """Run git and return its stdout, raising with git's own message on failure."""

    result = subprocess.run(
        ['git', *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode:
        # Without this the caller only ever sees "exit status 128".
        raise RuntimeError(f'git {" ".join(args)} failed: {result.stderr.strip()}')

    return result.stdout.strip()


def ref_exists(ref: str, *, cwd: Path) -> bool:
    """Whether *ref* resolves to a commit in the checkout at *cwd*."""

    result = subprocess.run(
        ['git', 'rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}'],
        cwd=cwd,
        check=False,
        capture_output=True,
    )

    return result.returncode == 0


def checkout_target(ref: str, *, cwd: Path) -> str:
    """The ref to check out for *ref*.

    A tag is immutable, so it is used as given. A branch is not: ``git fetch``
    updates ``origin/<branch>`` and leaves the local branch where it was, so
    checking out the local one would silently rebuild from a stale snapshot.
    """

    remote = f'origin/{ref}'

    return remote if ref_exists(remote, cwd=cwd) else ref


def sync(name: str, *, update: bool = False) -> Path:
    """Clone or update one upstream repository and return its path."""

    source = SOURCES[name]
    path = CACHE / name

    if not (path / '.git').is_dir():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f'  cloning {source.url}')
        run_git('clone', '--filter=blob:none', '--no-checkout', source.url, str(path))
    elif update:
        print(f'  fetching {name}')
        run_git('fetch', '--filter=blob:none', 'origin', cwd=path)

    run_git('checkout', '--force', checkout_target(source.ref, cwd=path), cwd=path)
    revision = run_git('rev-parse', '--short', 'HEAD', cwd=path)
    print(f'  {name}: {source.ref} @ {revision}')

    return path


def sync_all(*, update: bool = False) -> dict[str, Path]:
    """Clone or update every upstream repository, returning each checkout path."""

    print('Syncing upstream sources')

    return {name: sync(name, update=update) for name in SOURCES}


def repo_date(path: Path) -> str:
    """The author date of the checked-out commit, as YYYY-MM-DD."""

    return run_git('log', '-1', '--format=%ad', '--date=short', cwd=path)
