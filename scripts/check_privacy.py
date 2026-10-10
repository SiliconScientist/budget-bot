#!/usr/bin/env python3
"""Check indexed files without reading private working files or printing values."""
import hashlib
import json
from pathlib import PurePosixPath
import re
import subprocess
import sys


MANIFEST = "tests/fixtures/synthetic-manifest.json"
PRIVATE_DIRS = {"data", "exports", ".private", ".aws", ".ssh"}
PRIVATE_SUFFIXES = {
    ".csv", ".tsv", ".xlsx", ".xls", ".pdf", ".ofx", ".qfx", ".qif",
    ".db", ".sqlite", ".sqlite3", ".pem", ".key", ".p12", ".pfx",
    ".bundle", ".zip", ".gz", ".bak", ".log",
}
PATTERNS = {
    "account number label": rb"\b(?:debit|credit)\d{4,}\b",
    "bank reference": rb"\b(?:JPM[A-Za-z0-9]{6,}|PPD ID:\s*\d+)",
    "private key": rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "credential": rb"\b(?:AKIA[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{20,})",
    "credential assignment": rb"(?i)\b(?:password|api_key|access_token|client_secret)\s*[=:]\s*[\"'][^\"'\r\n]{8,}[\"']",
    "local home path": rb"/(?:Users|home)/[A-Za-z0-9_.-]+/",
}


def git(*args):
    return subprocess.check_output(["git", *args])


def main():
    entries = {}
    for item in git("ls-files", "--stage", "-z").split(b"\0"):
        if item:
            metadata, path = item.split(b"\t", 1)
            mode, oid, stage = metadata.decode().split()
            if stage != "0":
                print("Privacy check: resolve merge conflicts first.", file=sys.stderr)
                return 1
            entries[path.decode()] = (mode, oid)
    approved = {}
    if MANIFEST in entries:
        approved = json.loads(git("cat-file", "blob", entries[MANIFEST][1]))
        if not isinstance(approved, dict):
            raise ValueError("Fixture manifest must be an object")
    failures = []
    for name, (mode, oid) in entries.items():
        path = PurePosixPath(name)
        if mode not in {"100644", "100755"}:
            failures.append((name, "symlink or submodule requires review"))
            continue
        content = git("cat-file", "blob", oid)
        private = (
            bool(set(path.parts) & PRIVATE_DIRS)
            or path.name in {"config.toml", "category.toml", ".env", ".envrc"}
            or path.name.startswith(".env.")
            or path.suffix.lower() in PRIVATE_SUFFIXES
        )
        fixture = (name.startswith("tests/fixtures/") and path.suffix == ".csv"
                   and approved.get(name) == hashlib.sha256(content).hexdigest())
        if private and not fixture:
            failures.append((name, "private data path or unapproved fixture"))
        if b"\0" in content:
            failures.append((name, "binary file requires review"))
            continue
        for label, pattern in PATTERNS.items():
            if re.search(pattern, content):
                failures.append((name, label))
        for email in re.findall(rb"[\w.+-]+@([\w.-]+\.[A-Za-z]{2,})", content):
            if email.lower() not in {b"example.com", b"example.org", b"users.noreply.github.com"}:
                failures.append((name, "non-example email address"))
    for name, reason in failures:
        print(f"Privacy check: {name}: {reason}", file=sys.stderr)
    if failures:
        print("Unstage private files; use fictional fixtures. See README privacy guidance.",
              file=sys.stderr)
        return 1
    print(f"Privacy check passed ({len(entries)} indexed files).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (subprocess.CalledProcessError, ValueError, KeyError) as exc:
        print(f"Privacy check could not complete ({type(exc).__name__}).", file=sys.stderr)
        sys.exit(1)
