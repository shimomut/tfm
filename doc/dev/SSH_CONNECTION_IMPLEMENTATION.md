# SSH/SFTP Connection Implementation

TFM's remote browsing runs on `src/tfm_ssh_connection.py` (`SSHConnection` +
`SSHConnectionManager`), which drives OpenSSH's `ssh` / `sftp` CLIs in batch mode
over a shared control master. This document records the non-obvious correctness
and packaging behaviors that make SFTP browsing robust — the reasons certain
things are done a specific way, so they aren't accidentally undone.

Related docs:
- Control-master sharing and its check-caching — `SSH_CONTROL_MASTER_EXPLANATION.md`,
  `SSH_CONTROL_MASTER_OPTIMIZATION_IMPLEMENTATION.md`
- Bulk stat batching — `SFTP_BULK_STAT_OPTIMIZATION_IMPLEMENTATION.md`
- The polymorphic `Path` layer that exposes remote paths to the rest of TFM —
  `PATH_POLYMORPHISM_SYSTEM.md`

---

## SFTP path handling

Every remote operation builds an `sftp` batch command as a **string**. So any
path that reaches a command must be quoted, must be normalized, and — for
directory listings — must be parsed before it is filtered. All three rules live
in `SSHConnection`.

### Path quoting — `_quote_path()`

SFTP batch mode splits each command on whitespace, so a filename containing
spaces or special characters would be mis-parsed as several arguments and the
operation would fail.

`_quote_path(path)` escapes any embedded `"` (→ `\"`) and wraps the whole path in
double quotes. Every command construction routes its paths through it —
`list_directory`, `stat`, `read_file`, `write_file`, `delete_file`,
`delete_directory`, `create_directory`, `rename`, and glob. For example a copy
becomes `get "/remote/my file.txt" "/tmp/tmpXXX"`.

This correctly handles spaces, parentheses, brackets, embedded quotes, and
runs of multiple spaces.

### Path normalization — `posixpath.normpath()`

Search and path-join operations can hand SFTP paths carrying runaway `./././…`
or `..` segments. Left as-is, these both blow up the SFTP command (a real
observed failure was a path ending in dozens of repeated `/.`) and pollute the
path cache with many equivalent-but-distinct keys.

`list_directory()` and `stat()` normalize `remote_path` with
`posixpath.normpath()` before the cache lookup and before any SFTP call. That
collapses `//`, strips `/./`, resolves `/a/../b`, and trims trailing slashes. It
is a cheap string operation; already-normal paths pass through unchanged, and
normalizing equivalent paths actually raises the cache hit rate.

### Dot-entry filtering — parse first, then filter

SFTP's `ls -la` emits `.` and `..` rows, and in that output the filename field
is a **full path** (`…/projects/tfm/.`), not a bare `.`. So filtering on the raw
line (e.g. `line.endswith(' .')`) silently misses them.

`list_directory()` instead filters **after** `_parse_ls_line()` has extracted the
basename: `if entry['name'] in ('.', '..'): continue`.

Getting this wrong is severe, not cosmetic: a surviving `.` entry re-enters the
current directory, so a recursive walk loops and every yielded entry appears
named `.`. The visible symptom is subtle — e.g. a `*.py` search returns 0
results rather than obviously hanging. The general lesson: parse structured
command output into fields first, then filter on the parsed fields.

---

## Connection establishment

TFM shares a single OpenSSH control master per host. Establishing it reliably —
especially from a packaged macOS app — required the three behaviors below.

### Control-socket location & per-process isolation

Control sockets live at `~/.tfm/ssh_sockets/tfm-ssh-{hostname_hash}-{pid}`
(created in `SSHConnection.__init__`), **not** under `tempfile.gettempdir()` /
`/tmp`.

- **Why the home directory:** a DMG-mounted or otherwise sandbox-restricted app
  may have limited `/tmp` access, and socket creation there can fail silently.
  The failure surfaces as SSH's opaque `Connection closed by UNKNOWN port 65535`.
  The user's home directory is always writable in that context, and keeping
  sockets under `~/.tfm/` (next to `config.py` and `ssh_cache.json`) makes them
  easy to inspect and clean up.
- **Why the `{pid}`:** each TFM process gets its own control socket, so one
  instance exiting and deleting its socket cannot break another instance
  connected to the same host.
- Socket paths must stay short — the Unix-domain socket path limit is ~104
  characters on most systems.

### Foreground control master (no `-f`)

`_establish_control_master()` runs `ssh -N` (no remote command) **without** the
`-f` (fork-to-background) flag.

With `-f`, `ssh` backgrounds immediately and the parent returns success even when
a `ProxyCommand` hangs — so a failed connection can be neither detected nor timed
out. Running in the foreground instead lets TFM poll for the control socket to
appear, apply a timeout, and capture stderr on failure. `ControlPersist` keeps
the socket alive after TFM terminates the master process once the socket exists.

### Packaged-app PATH (macOS DMG)

A DMG-mounted app does not inherit the user's shell `PATH`. SSH configs that use
a `ProxyCommand` shelling out to `aws`, `gcloud`, etc. therefore can't find those
tools and fail with the same `port 65535` error.

`macos_app/src/TFMAppDelegate.m` fixes this in `setupEnvironmentPath`, called
before the TFM module is imported. It prepends the common tool locations —
`/usr/local/bin`, `/opt/homebrew/bin`, `/opt/local/bin`, `~/bin`, `~/.local/bin`,
and the `~/Library/Python/3.x/bin` dirs — to `PATH` via `setenv`, and mirrors the
result into Python's `os.environ` so every subprocess (and thus the
`ProxyCommand`) can resolve those tools.

---

Related code: `src/tfm_ssh_connection.py`, `macos_app/src/TFMAppDelegate.m`.
