"""Pins and hand-maintained mappings for the documentation build.

Everything the build produces is derived from the two upstream repositories
pinned below. Nothing under ``docs/`` is edited by hand -- see ``content/`` for
the pages that are written for this site.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / '.cache'
CONTENT = ROOT / 'content'
DOCS = ROOT / 'docs'

# --- upstream sources -------------------------------------------------------

#: The collectd release this site documents.
VERSION = '5.12.0'


@dataclass(frozen=True)
class Source:
    """An upstream repository and the ref this site is built from."""

    url: str
    ref: str


@dataclass(frozen=True)
class Companion:
    """A wiki page appended to another page rather than given one of its own."""

    owner: str
    heading: str


@dataclass(frozen=True)
class FilterItem:
    """A match or target documented as an ``=item`` under a manpage heading."""

    heading: str
    key: str
    title: str


SOURCES = {
    'collectd': Source(
        url='https://github.com/collectd/collectd.git',
        ref=f'collectd-{VERSION}',
    ),
    'wiki': Source(
        url='https://github.com/collectd/collectd.wiki.git',
        ref='master',
    ),
}

#: Manpages shipped by collectd, in the order they should appear in the nav.
MANPAGES = [
    ('collectd.conf', 5, 'Configuration file'),
    ('collectd', 1, 'The daemon'),
    ('collectdctl', 1, 'Control utility'),
    ('collectdmon', 1, 'Monitoring wrapper'),
    ('collectd-nagios', 1, 'Nagios check command'),
    ('collectd-tg', 1, 'Traffic generator'),
    ('types.db', 5, 'Data-set definitions'),
    ('collectd-email', 5, 'Email plugin protocol'),
    ('collectd-exec', 5, 'Exec plugin protocol'),
    ('collectd-java', 5, 'Java plugin'),
    ('collectd-lua', 5, 'Lua plugin'),
    ('collectd-perl', 5, 'Perl plugin'),
    ('collectd-python', 5, 'Python plugin'),
    ('collectd-snmp', 5, 'SNMP plugin'),
    ('collectd-threshold', 5, 'Threshold checking'),
    ('collectd-unixsock', 5, 'UNIX socket protocol'),
]

# --- plugin identity --------------------------------------------------------

#: Wiki page stems whose plugin name cannot be derived from the page title.
WIKI_PLUGIN_ALIASES = {
    'Plugin-APC-UPS': 'apcups',
    'Plugin-E-Mail': 'email',
    'Plugin-IntelRDT': 'intel_rdt',
    'Plugin-Carbon': 'write_graphite',
    'Plugin-OpenTSDB': 'write_tsdb',
    'Plugin-MongoDB': 'write_mongodb',
}

#: Wiki pages that document one aspect of a plugin rather than a plugin of
#: their own. They are appended to the owning plugin's page.
WIKI_COMPANIONS = {
    'Plugin-Aggregation-Config': Companion('aggregation', 'Configuration examples'),
    'Plugin-GenericJMX-Config': Companion('GenericJMX', 'Configuration examples'),
    'Plugin-Intel-PMU-Config': Companion('intel_pmu', 'Configuration examples'),
    'Plugin-SNMP-Config': Companion('snmp', 'Configuration examples'),
    'Plugin-Tail-Config': Companion('tail', 'Configuration examples'),
    'Plugin-cURL-Config': Companion('curl', 'Configuration examples'),
    'Plugin-cURL-XML-Config': Companion('curl_xml', 'Configuration examples'),
    'Plugin-connectivity-Config': Companion('connectivity', 'Configuration examples'),
    'Plugin-cURL-JSON-ArangoDB': Companion('curl_json', 'Example: ArangoDB'),
    'Plugin-cURL-JSON-Cherokee': Companion('curl_json', 'Example: Cherokee'),
    'Plugin-cURL-JSON-phpfpm': Companion('curl_json', 'Example: PHP-FPM'),
    'Plugin-exec-ksm.sh': Companion('exec', 'Example: KSM statistics'),
    'Plugin-exec-munin.px': Companion('exec', 'Example: Munin plugin bridge'),
    'Plugin-exec-redis.sh': Companion('exec', 'Example: Redis statistics'),
    'Plugin-exec-solusvm-bandwidth.sh': Companion('exec', 'Example: SolusVM bandwidth'),
    'Plugin-haproxy-stat.sh': Companion('exec', 'Example: HAProxy statistics'),
    'Plugin-haproxy.rb': Companion('exec', 'Example: HAProxy statistics (Ruby)'),
}

#: Plugins built by 5.12.0 that take no configuration, so the manpage has no
#: section for them. Without this list they would be missing from the site.
#: Derived from configure.ac; kept explicit so the build can verify it.
CONFIGLESS_PLUGINS = [
    'apple_sensors',
    'contextswitch',
    'drbd',
    'entropy',
    'fscache',
    'ipc',
    'ipvs',
    'madwifi',
    'multimeter',
    'netstat_udp',
    'numa',
    'pf',
    'serial',
    'synproxy',
    'tape',
    'uptime',
    'users',
    'wireless',
    'xmms',
    'zfs_arc',
    'zone',
]

#: Filter matches and targets. They are AC_PLUGIN entries but are documented
#: as part of the filter chain, not as plugins.
FILTER_PLUGIN_PREFIXES = ('match_', 'target_')

#: Plugins named in the manpage that no longer exist in the 5.12.0 source.
REMOVED_FROM_SOURCE = {'curl_jolokia'}

# --- filter chains ---------------------------------------------------------

#: Matches and targets documented as ``=item`` entries under the manpage's
#: "Available matches" / "Available targets" headings, keyed by plugin name.
FILTER_ITEMS = {
    'match_regex': FilterItem('Available matches', 'regex', 'Match: regex'),
    'match_timediff': FilterItem('Available matches', 'timediff', 'Match: timediff'),
    'match_value': FilterItem('Available matches', 'value', 'Match: value'),
    'match_empty_counter': FilterItem(
        'Available matches', 'empty_counter', 'Match: empty_counter'
    ),
    'match_hashed': FilterItem('Available matches', 'hashed', 'Match: hashed'),
    'target_notification': FilterItem('Available targets', 'notification', 'Target: notification'),
    'target_replace': FilterItem('Available targets', 'replace', 'Target: replace'),
    'target_set': FilterItem('Available targets', 'set', 'Target: set'),
}

#: Targets that ship with collectd but are not documented as their own item in
#: the manpage (built-ins, or documented only on the wiki).
FILTER_EXTRA = {
    'target_scale': 'Target: scale',
    'target_v5upgrade': 'Target: v5upgrade',
    'target_write': 'Target: write',
}

#: Wiki pages backing the filter reference.
WIKI_FILTER_PAGES = {
    'Match-RegEx': 'match_regex',
    'Match-TimeDiff': 'match_timediff',
    'Match-Value': 'match_value',
    'Match-Empty-Counter': 'match_empty_counter',
    'Match-Hashed': 'match_hashed',
    'Target-Notification': 'target_notification',
    'Target-Replace': 'target_replace',
    'Target-Set': 'target_set',
    'Target-Scale': 'target_scale',
    'Target-v5-upgrade': 'target_v5upgrade',
    'Target-Write': 'target_write',
}

WIKI_FILTER_COMPANIONS = {
    'Match-Hashed-Config': Companion('match_hashed', 'Configuration examples'),
}

# --- wiki triage ------------------------------------------------------------

#: Pages excluded outright: meeting minutes, per-release notes, event pages and
#: documentation for plugins that no longer ship.
WIKI_EXCLUDE_PATTERNS = [
    r'^Minutes',
    r'^Version-\d',
    r'^List-of-versions$',
    r'^Events',
    r'^Hackathon',
    r'^GSoC',
    r'^Google-Summer',
    r'-Tests$',
]

#: Removed or third-party plugins with a wiki page but no 5.12.0 source, plus
#: pages about other collectd releases.
WIKI_EXCLUDE_PAGES = {
    'Plugin-CvmFS',
    'Plugin-LVM',
    'Plugin-Monitorus',
    'Plugin-OpenVZ',
    'Plugin-WPAR',
    'Plugin-ZeroMQ',
    'Plugin-puppet-reports',
    'Plugin-Write-Redis-Design',
    'collectd-6',
    'V3-to-v4-migration-guide',
    'V5-to-v6-migration-guide',
    '_Sidebar',
    'Home',
}

#: Wiki pages that become site pages outside the plugin reference, grouped by
#: the section they belong to. Anything not listed here is dropped.
WIKI_SECTIONS: dict[str, list[tuple[str, str]]] = {
    'concepts': [
        ('First-steps', 'First steps'),
        ('Data-set', 'Data sets'),
        ('Data-source', 'Data sources'),
        ('Value-list', 'Value lists'),
        ('Naming-schema', 'Naming schema'),
        ('Interval', 'Intervals'),
        ('Global-cache', 'The global cache'),
        ('FQDNLookup', 'FQDN lookup'),
        ('Notifications-and-thresholds', 'Notifications and thresholds'),
        ('Meta-Data-Interface', 'Meta data'),
        ('High-resolution-time-format', 'High-resolution time format'),
        ('Troubleshooting', 'Troubleshooting'),
    ],
    'protocols': [
        ('Binary-protocol', 'Binary network protocol'),
        ('Plain-text-protocol', 'Plain text protocol'),
        ('JSON', 'JSON representation'),
    ],
    'contributing': [
        ('Plugin-architecture', 'Plugin architecture'),
        ('Inside-the-RRDtool-plugin', 'Inside the RRDtool plugin'),
        ('Notification-t', 'notification_t'),
        ('User-data-t', 'user_data_t'),
        ('Coding-style', 'Coding style'),
        ('Submitting-patches', 'Submitting patches'),
        ('Gerrit', 'Code review with Gerrit'),
        ('Release-process', 'Release process'),
        ('Core-file', 'Reporting a crash'),
        ('Pkg-config', 'pkg-config integration'),
        ('Repository', 'Package repositories'),
        ('Mailing-list', 'Mailing list'),
    ],
}
