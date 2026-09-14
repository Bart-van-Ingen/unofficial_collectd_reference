<p align="center">
   <img src="content/assets/images/logo.png" alt="Collectd unofficial reference logo" width="30%" />
</p>

# Collectd unofficial reference

> [!WARNING]
> This is an **unofficial** project and is not directly affiliated with
> [collectd](https://github.com/collectd/collectd). I offer it as a way to
> navigate collectd's existing documentation more easily; the authoritative
> sources remain the collectd repository and its wiki.

A single documentation site for **collectd 5.12.0**, generated from the two
places collectd's documentation actually lives:

- [`collectd/collectd`](https://github.com/collectd/collectd) at tag
  `collectd-5.12.0` — the 16 manual pages (`src/*.pod`) and the authoritative
  plugin list from `configure.ac`.
- [`collectd/collectd.wiki`](https://github.com/collectd/collectd.wiki) —
  plugin descriptions, dependencies, caveats, examples and concept pages.

Built with [Zensical](https://zensical.org). Dependencies are managed with
[uv](https://docs.astral.sh/uv/).

<h2 align="center">
   <a href="https://bart-van-ingen.github.io/collectd_unofficial_reference/">Read the documentation &rarr;</a>
</h2>

## Usage

```console
$ uv sync                       # install zensical
$ uv run collectd-docs          # generate docs/ and snippets/
$ uv run zensical serve         # preview on http://localhost:8000
```

`uv run collectd-docs --update` re-fetches the upstream repositories first.
The first run clones them into `.cache/` (about 60 MB).

## Publishing

[`.github/workflows/publish.yml`](.github/workflows/publish.yml) builds the
site and deploys it to GitHub Pages on every push to `main`, or on demand from
the Actions tab. Pages must be enabled once under **Settings → Pages**, with
**GitHub Actions** as the source.

Pages serves the site under `/collectd_unofficial_reference/`, not at the root,
so the workflow passes the published address to the build as `SITE_URL`.
Every internal link is prefixed with its path. To reproduce the published
build locally:

```console
$ SITE_URL=https://bart-van-ingen.github.io/collectd_unofficial_reference/ uv run collectd-docs
$ uv run zensical build
```

## How it works

`docs/` and `snippets/` are **generated in full on every run** and are not
checked in. The only hand-written pages are in `content/`, which is copied over
the generated tree at the end of the build.

### The configuration windows

Each plugin page ends with a framed section headed *from `collectd.conf(5)`*.
That frame is a window onto part of the manual page, not a copy of it:

1. `tools/build.py` splits `src/collectd.conf.pod` into one fragment per
   plugin and writes them to `snippets/conf/<plugin>.md`.
2. The plugin page includes its fragment with a `pymdownx.snippets` directive.
3. The [full `collectd.conf(5)` page](docs/manpages/collectd.conf.md) includes
   *the same fragments*, each introduced by a link back to the plugin page.

One file, two views. They cannot drift apart, and the cross-links run both
ways — which was the main thing the upstream documentation was missing.

## Layout

| Path | What it is |
|---|---|
| `tools/pod.py` | Perl POD parser (the manual pages' source format) |
| `tools/render.py` | POD tree → Markdown, with configuration options as definition lists |
| `tools/wiki.py` | Wiki page normaliser: infoboxes, wikilinks, dead-link handling |
| `tools/sources.py` | Clones and pins the upstream repositories |
| `tools/config.py` | The release pin, plugin name aliases and wiki triage tables |
| `tools/build.py` | Assembles every page and regenerates the nav in `zensical.toml` |
| `content/` | The only hand-written pages |

## Editorial scope

Following the current release only:

- Meeting minutes, per-release notes and event pages are excluded.
- Pages about collectd 6 and the old migration guides are excluded.
- Wiki pages for plugins not present in the 5.12.0 source tree are excluded.
- Third-party front-ends and companion projects are excluded.

Plugins that ship in 5.12.0 but take no configuration have no section in
`collectd.conf(5)`. They still get a page, marked as taking no configuration —
without this, 21 real plugins (`users`, `uptime`, `entropy`, `zfs_arc` and
others) would be missing entirely.

Every wiki reference that could not be turned into a working link is listed in
the generated link report at `/about/link-report/`, grouped by cause.

## Licensing

The collectd sources and wiki are licensed **GPLv2**, and so is the text this
site renders. The build tooling in `tools/` is the only original code here.
