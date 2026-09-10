# About this site

## What it covers

collectd **{{ version }}**, the current stable release, tagged
`collectd-{{ version }}` and released {{ release_date }}. Wiki content is taken
from the state of the wiki on {{ wiki_date }}.

Nothing here describes collectd 6, which is still in release-candidate form, and
nothing describes plugins that shipped in earlier releases and have since been
removed.

## Where the content comes from

| Source | Used for |
|---|---|
| [`collectd/collectd`](https://github.com/collectd/collectd) at `collectd-{{ version }}` | All 16 manual pages, including the configuration reference, and the authoritative list of plugins from `configure.ac` |
| [`collectd/collectd.wiki`](https://github.com/collectd/collectd.wiki) | Plugin descriptions, dependencies, caveats, example configurations and the conceptual pages |

Both are the collectd project's own documentation and are licensed **GPLv2**.
This site is a re-presentation of them, not a rewrite: the text is the
project's, generated from the sources at build time rather than copied, so it
stays in step with whatever those sources say.

## The configuration windows

Each plugin page ends with a framed section headed *from `collectd.conf(5)`*.
That frame is a window onto one part of the manual page. The build extracts
each `Plugin` section from `src/collectd.conf.pod` into a single fragment, and
both the plugin page and the [full configuration
reference](/manpages/collectd.conf/) include that one fragment.

The link runs both ways: the frame links into the corresponding place in the
configuration reference, and every plugin section of the configuration
reference links back out to the plugin page for the prose.

## Rebuilding

```console
$ uv run collectd-docs --update   # re-fetch upstream, regenerate docs/
$ uv run zensical serve           # preview on localhost:8000
```

`docs/` and `snippets/` are generated in full on every run and are not checked
in. The hand-written pages — this one and the front page — live in `content/`.

## What was left out

- Meeting minutes and per-release notes from the wiki.
- Pages about collectd 6 and the 3-to-4 and 5-to-6 migration guides.
- Wiki pages for plugins that are not in the {{ version }} source tree.
- Third-party front-ends and companion projects, most of which are unmaintained.

Wiki links that pointed at any of the above, or at the retired
`collectd.org/wiki/` site, are reported in the
[link report](/about/link-report/).
