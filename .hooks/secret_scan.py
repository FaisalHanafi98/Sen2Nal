#!/usr/bin/env python3
# GENERATED from core@c71f6db - source: hooks/lib/secret_scan.py
# hook: secret-scan
# mode: gate
# events: pre-commit
# timeout_ms: 2000
"""Block commits containing high-signal secret patterns.

Gate philosophy: high precision only. Length guards keep teaching examples
like "sk-proj-xxxxx" from tripping it; broad advisory patterns belong in
`ai doctor`, not here. Bypass is a deliberate act: move the value to the
credential store instead.

Staged mode scans complete index blobs, including binary bytes and symlink
targets, without following worktree paths. UTF BOMs are decoded explicitly;
otherwise every byte is retained through UTF-8 surrogate escaping. Detection
is limited to the listed patterns, not encrypted/encoded credential discovery.
Oversized blobs, gitlinks, conflicts and failed object reads require review and
return 2 rather than silently passing. Existing secret matches return 1.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PATTERNS = [
    ("anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("api key (sk-)", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("github token", re.compile(r"\b(?:ghp|gho|ghs|ghr)_[A-Za-z0-9]{36}\b|github_pat_[A-Za-z0-9_]{22,}")),
    ("aws access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("google api key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}")),
    ("slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]
MAX_BYTES = 1_000_000
GIT_TIMEOUT_SECONDS = 2


class ScanError(Exception):
    """The selected content could not be inspected under this gate's policy."""


def git_output(args, data=None):
    try:
        result = subprocess.run(['git', '--no-replace-objects', '--no-lazy-fetch',
                                 '--no-optional-locks', *args],
                                input=data, capture_output=True,
                                timeout=GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ScanError('Git inspection was unavailable or timed out') from exc
    if result.returncode:
        # Git stderr can contain arbitrary repository bytes; do not echo it.
        raise ScanError('Git inspection failed')
    return result.stdout


def staged_entries():
    raw = git_output(['diff', '--cached', '--raw', '-z', '--no-abbrev',
                      '--no-renames', '--no-ext-diff', '--no-textconv',
                      '--ignore-submodules=none', '--diff-filter=ACMTU'])
    if not raw:
        return []
    parts = raw.split(b'\0')
    if parts[-1] or len(parts) % 2 != 1:
        raise ScanError('Invalid staged change listing')
    entries = []
    for pos in range(0, len(parts) - 1, 2):
        header, path = parts[pos:pos + 2]
        fields = header[1:].split() if header.startswith(b':') else []
        if len(fields) != 5 or not path:
            raise ScanError('Invalid staged change entry')
        _, mode, _, oid, status = fields
        if (mode not in (b'100644', b'100755', b'120000') or
                status not in (b'A', b'C', b'M', b'T') or
                not re.fullmatch(rb'(?:[0-9a-f]{40}|[0-9a-f]{64})', oid) or
                not oid.strip(b'0')):
            raise ScanError('Unsupported or unresolved staged entry: ' + ascii(os.fsdecode(path)))
        entries.append((os.fsdecode(path), oid))
    return entries


def blob_info(line, expected_oid):
    fields = line.split()
    if (len(fields) != 3 or fields[0] != expected_oid or
            fields[1] != b'blob' or not fields[2].isdigit()):
        raise ScanError('Staged object metadata could not be verified')
    return int(fields[2])


def read_blob_batch(entries):
    response = git_output(['cat-file', '--batch'],
                          b''.join(oid + b'\n' for _, oid, _ in entries))
    cursor = 0
    for path, oid, expected_size in entries:
        end = response.find(b'\n', cursor)
        if end < 0 or blob_info(response[cursor:end], oid) != expected_size:
            raise ScanError('Staged object response was inconsistent')
        cursor = end + 1
        raw = response[cursor:cursor + expected_size]
        cursor += expected_size
        if len(raw) != expected_size or response[cursor:cursor + 1] != b'\n':
            raise ScanError('Staged object contents were incomplete')
        cursor += 1
        yield path, raw
    if cursor != len(response):
        raise ScanError('Unexpected staged object response')


def staged_contents():
    entries = staged_entries()
    if not entries:
        return
    info = git_output(['cat-file', '--batch-check'],
                      b''.join(oid + b'\n' for _, oid in entries)).splitlines()
    if len(info) != len(entries):
        raise ScanError('Staged object metadata was incomplete')
    batch, size = [], 0
    for (path, oid), line in zip(entries, info):
        blob_size = blob_info(line, oid)
        if blob_size > MAX_BYTES:
            raise ScanError('Staged blob exceeds scan limit; review required: ' + ascii(path))
        if batch and size + blob_size > MAX_BYTES:
            yield from read_blob_batch(batch)
            batch, size = [], 0
        batch.append((path, oid, blob_size))
        size += blob_size
    if batch:
        yield from read_blob_batch(batch)


def scan_bytes(path, raw):
    if len(raw) > MAX_BYTES:
        raise ScanError('Content exceeds scan limit; review required: ' + ascii(path))
    try:
        if raw.startswith((b'\xff\xfe\0\0', b'\0\0\xfe\xff')):
            text = raw.decode('utf-32')
        elif raw.startswith((b'\xff\xfe', b'\xfe\xff')):
            text = raw.decode('utf-16')
        else:
            text = raw.decode('utf-8', errors='surrogateescape')
    except UnicodeError as exc:
        raise ScanError('Invalid BOM encoding; review required: ' + ascii(path)) from exc
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in PATTERNS:
            if pattern.search(line):
                hits.append((path, lineno, name))
    return hits


def scan_file(path):
    try:
        with open(path, 'rb') as source:
            raw = source.read(MAX_BYTES + 1)
    except OSError as exc:
        raise ScanError('Cannot read selected file: ' + ascii(path)) from exc
    return scan_bytes(path, raw)


def log_telemetry(exit_code, n_files):
    # Hook logs double as the pruning-data substrate (spec §3). Never let
    # logging failure break the gate.
    try:
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ai-core"
        base.mkdir(parents=True, exist_ok=True)
        line = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "hook": "secret-scan", "exit": exit_code, "files": n_files}
        with open(base / "telemetry.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
    except OSError:
        pass


def main(argv):
    hits, n_files = [], 0
    try:
        if argv == ['--staged']:
            for path, raw in staged_contents():
                n_files += 1
                hits.extend(scan_bytes(path, raw))
        elif any(arg.startswith('--') for arg in argv):
            raise ScanError('Use --staged alone or supply explicit file paths')
        else:
            for path in argv:
                n_files += 1
                hits.extend(scan_file(path))
    except ScanError as exc:
        print('secret-scan: REVIEW REQUIRED - ' + str(exc), file=sys.stderr)
        log_telemetry(2, n_files)
        return 2
    if hits:
        print("secret-scan: BLOCKED - possible credentials in the commit:", file=sys.stderr)
        for path, lineno, name in hits:
            print(f"  {ascii(path)}:{lineno}: {name}", file=sys.stderr)
        print("Move the value to the credential store or .env (gitignored), then retry.", file=sys.stderr)
        log_telemetry(1, n_files)
        return 1
    log_telemetry(0, n_files)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
