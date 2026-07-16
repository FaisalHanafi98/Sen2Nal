#!/usr/bin/env python3
# hook: secret-scan
# mode: gate
# events: pre-commit
# timeout_ms: 2000
"""Block commits containing high-signal secret patterns.

Gate philosophy: high precision only. Length guards keep teaching examples
like "sk-proj-xxxxx" from tripping it; broad advisory patterns belong in
`ai doctor`, not here. Bypass is a deliberate act: move the value to the
credential store instead.
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


def staged_files():
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACM"],
        capture_output=True, text=True,
    )
    return [f for f in r.stdout.split("\0") if f]


def scan_file(path):
    p = Path(path)
    if not p.is_file() or p.stat().st_size > MAX_BYTES:
        return []
    raw = p.read_bytes()
    if b"\x00" in raw[:8192]:
        return []
    text = raw.decode("utf-8", errors="ignore")
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in PATTERNS:
            if pattern.search(line):
                hits.append((path, lineno, name))
    return hits


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
    files = staged_files() if "--staged" in argv else [a for a in argv if not a.startswith("--")]
    hits = []
    for f in files:
        hits.extend(scan_file(f))
    if hits:
        print("secret-scan: BLOCKED - possible credentials in the commit:", file=sys.stderr)
        for path, lineno, name in hits:
            print(f"  {path}:{lineno}: {name}", file=sys.stderr)
        print("Move the value to the credential store or .env (gitignored), then retry.", file=sys.stderr)
        log_telemetry(1, len(files))
        return 1
    log_telemetry(0, len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
