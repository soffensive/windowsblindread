# windowsblindread

A comprehensive list of files and paths to probe when arbitrary files can be read on a Microsoft Windows operating system, including LFI and path traversal testing.

[windows-files.txt](windows-files.txt) is the ready-to-use combined wordlist: one absolute path per line, forward slashes, no headers. It includes all original paths plus additional Windows, application, database, deployment, and user-profile candidates. No network scanner or third-party Python dependencies are needed.

The goal is broad coverage, including legacy systems and optional software. A path is a candidate, not a guarantee of existence or readability. Installation roots, versions, usernames, permissions, file locks, and application configuration affect results. Some files are binary or large; a failed read does not establish that a path is absent. The original list also contains directories, which are retained for compatibility.

## Generate a wordlist

Python 3.9 or newer:

```sh
# Rebuild the distributed list with every category and the original corpus.
python3 tools/generate.py --output windows-files.txt

# Include multiple drives and known usernames.
python3 tools/generate.py --drive c --drive d --drive e --username Alice --username svc_web --output /tmp/windows-expanded.txt

# Add discovered application locations, preserving case and spaces.
python3 tools/generate.py --root 'webapps=D:/Sites/CustomerPortal' --root 'tomcat=E:/Apps/Tomcat' --output /tmp/windows-custom.txt

# Select categories when useful; omitting --category includes everything.
python3 tools/generate.py --category windows --category iis --category webapps
python3 tools/generate.py --list-categories

# Use native Windows separators if required by the input.
python3 tools/generate.py --separator backslash --output /tmp/windows-backslashes.txt
```

`--drive` replaces the default `c` drive selection and expands all C-drive candidates onto each supplied drive. Explicit custom roots on other drives are retained as supplied. `--username` adds profiles under both `Users` and `Documents and Settings`, including the original Administrator-relative paths when `legacy` is selected. Default profile candidates also include system and service accounts. `--root CATEGORY=PATH` adds a root for that category; roots for unselected categories are not emitted. Use `--root profiles=PATH` for relocated profiles. Values are literal paths; the generator does not expand environment variables, discover users, or contact a target.

Output is deterministic and deduplicated by exact spelling. Existing lowercase paths remain lowercase, while supplied usernames and roots preserve case for case-sensitive directories. Path escaping, URL encoding, and traversal depth depend on the vulnerable input and should be applied by the consuming tool. Some real filenames contain a literal `%` (for example `microsoft-windows-powershell%4operational.evtx`); encode it as `%25` when paths are sent in a URL.

## Coverage and maintenance

- [data/legacy-paths.txt](data/legacy-paths.txt) preserves the original 4,906-line corpus, including application-specific, version-specific, GUID, and directory entries. Generation removes accidental surrounding whitespace and trailing directory slashes; it does not discard those candidates.
- [data/catalog.json](data/catalog.json) contains named groups of candidate roots and relative filenames. Each root is combined with that group's filenames. `{profile}` expands to the default and supplied user profiles. This keeps new versions and installation roots easy to add without hand-maintaining thousands of combinations.
- Catalog groups cover Windows and boot files, unattended installation, Active Directory (NTDS), IIS and .NET, web application and CMS files, Apache, nginx, PHP, Tomcat, JBoss/WildFly, MySQL/MariaDB, PostgreSQL, SQL Server, MongoDB, Redis, Jenkins, OpenSSH, Docker, RabbitMQ, FileZilla, phpMyAdmin, Roundcube, Azure App Service, AnyDesk, UltraVNC, TeamViewer, SQL Server setup logs, Maven, monitoring, Elasticsearch, and developer/user configuration.
- Optional `reference` links document an application's file layout. Candidate roots include conventional and historical guesses; a reference does not verify every root/file combination. No Windows installation was used to validate these candidates.

For a new application, add a group with a unique `name`, nonempty `roots`, and relative `files`. For a versioned installation, add known candidate roots or supply an exact root at generation time. For dynamically named files, use discovered names rather than adding literal wildcard paths that a file-read API may not expand. Keep the complete list available even when adding focused categories. Add a primary documentation reference where available, regenerate, and run:

```sh
python3 tools/generate.py --output windows-files.txt
python3 -m unittest discover -s tests -v
```

Tests verify preservation of the original coverage, representative additional families, generated-file consistency, drive/profile expansion, custom roots, separators, and invalid options. CI runs the same checks.

The list cannot enumerate every custom site name, application version, profile, GUID, log date, or installation directory. For example, Firefox `logins.json` and `key4.db` live in randomly named profile folders; read `profiles.ini` first to find them. Use configuration files and other discovered paths to supply additional roots and usernames rather than treating the distributed list as exhaustive.

Original background: [Exploiting blind file reads / path traversal vulnerabilities on Microsoft Windows operating systems](https://soffensive.github.io/posts/web-app-sec/2018-06-19-exploiting-blind-file-reads-path-traversal-vulnerabilities-on-microsoft-windows-operating-systems/).
