#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""corpus.py -- fetch and track the OG(H)AM EpiDoc editions.

The editions live in a separate, *living* repository
(https://github.com/lguariento/og-h-am). This module keeps a local copy in
``data/origin/`` (gitignored) and a manifest in ``data/corpus-manifest.yaml``
(committed) recording exactly which state of that repository the outputs in this
one were generated from.

Two things follow from the corpus being a moving target:

1. **Fetching is incremental.** Only the ``XML/`` directory is retrieved -- a
   blobless, sparse, shallow clone, ~8 MB against the ~1.6 GB the full repository
   weighs with its images. Re-running fast-forwards the checkout, and the manifest
   diff then reports which editions actually changed.

2. **The manifest is the reproducibility anchor.** It holds the upstream commit,
   the fetch date and a git blob hash per file. The checkout itself is an input
   from elsewhere and is not committed here; the manifest is, so anyone can tell
   which corpus state produced ``out/`` and ``docs/`` -- and the place graph
   carries the same commit as PROV-O.

The blob hashes are git's own object ids, which lets the API fallback skip files
that have not changed without a git checkout being present at all.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

import yaml

URL = "https://github.com/lguariento/og-h-am.git"
WEB = "https://github.com/lguariento/og-h-am"
SUBDIR = "XML"                      # the only directory we need
SKIP_FILES = {"OG_H_AM.xml", "charDecl.xml"}   # corpus-level wrappers, not editions
# An edition is identified as such by its OG(H)AM id (I-COR-001, W-PEM-X02, ...);
# the corpus also carries template and test files. Mirrors places.OGHAM_ID_RE, so
# the manifest counts what the place layer will actually process.
OGHAM_ID_RE = re.compile(r"[A-Z]-[A-Z]{3}-[A-Z0-9]+")


def blob_sha(path: Path) -> str:
    """Git's object id for a file, so local files and the GitHub tree listing are
    directly comparable without downloading anything."""
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def has_editions(path: Path) -> bool:
    """True only if EpiDoc files are actually there -- an empty or half-fetched
    directory must not pass for a corpus."""
    return path.is_dir() and any(True for _ in itertools.islice(path.rglob("*.xml"), 1))


def resolve(explicit: Path | None, canonical: Path, fallback: Path,
            root: Path) -> tuple[Path, str]:
    """Corpus to read, and where that choice came from.

    Only ``data/origin/`` is discovered automatically. Earlier versions also picked
    up a sibling ``../og-h-am/`` checkout, which silently used whatever vintage
    happened to be lying next to the repository -- a stale clone then produced a
    graph that looked complete but was not. Anything outside ``data/origin/`` now
    has to be named explicitly.
    """
    if explicit is not None:
        return explicit, "--corpus"
    env = os.environ.get("OGHAM_CORPUS")
    if env and has_editions(Path(env)):
        return Path(env), "$OGHAM_CORPUS"
    if has_editions(canonical):
        return canonical, f"found {canonical.relative_to(root)}"
    return fallback, "fallback"


# --- manifest -----------------------------------------------------------------

def read_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        print(f"  ! {path.name} is unreadable ({exc}); treating the corpus as new")
        return {}


def scan(target: Path) -> dict[str, str]:
    """{path relative to the checkout: blob sha} for every EpiDoc file."""
    return {
        str(p.relative_to(target)).replace(os.sep, "/"): blob_sha(p)
        for p in sorted(target.rglob("*.xml"))
        if ".git" not in p.parts and not p.name.startswith(".")
    }


def git_remote(target: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(target), "remote", "get-url", "origin"],
                              check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def git_head(target: Path) -> dict:
    """Upstream commit of the checkout, empty if it is not a git working tree."""
    if not (target / ".git").exists():
        return {}
    try:
        out = subprocess.run(
            ["git", "-C", str(target), "log", "-1", "--format=%H%n%cI%n%s"],
            check=True, capture_output=True, text=True).stdout.splitlines()
        return {"commit": out[0], "commit_date": out[1], "commit_subject": out[2]}
    except (OSError, subprocess.CalledProcessError, IndexError):
        return {}


def diff(previous: dict, current: dict[str, str]) -> dict[str, list[str]]:
    """Which editions changed since the last fetch."""
    before = (previous or {}).get("files") or {}
    return {
        "added": sorted(set(current) - set(before)),
        "changed": sorted(k for k in set(current) & set(before) if current[k] != before[k]),
        "removed": sorted(set(before) - set(current)),
    }


def write_manifest(path: Path, target: Path, files: dict[str, str], root: Path) -> dict:
    editions = [f for f in files
                if Path(f).name not in SKIP_FILES and OGHAM_ID_RE.fullmatch(Path(f).stem)]
    manifest = {
        "source": URL,
        "subdirectory": SUBDIR,
        "checkout": str(target.relative_to(root)) if target.is_relative_to(root) else str(target),
        "fetched": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        **git_head(target),
        "file_count": len(files),
        "edition_count": len(editions),
        "files": dict(sorted(files.items())),
    }
    header = (
        "# Provenance of the OG(H)AM EpiDoc editions used by this repository.\n"
        "#\n"
        "# GENERATED by `python py/main.py --fetch-corpus`. Committed on purpose: the\n"
        "# checkout in data/origin/ is gitignored, so this file is the only record of\n"
        "# which upstream state produced out/ and docs/. `files` maps each edition to\n"
        "# its git blob hash, which is how the next fetch works out what changed.\n"
    )
    path.write_text(header + yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
                    encoding="utf-8")
    return manifest


def report(changes: dict[str, list[str]], previous: dict, limit: int = 12) -> None:
    """Print what moved upstream since the last fetch."""
    def names(keys):
        return [Path(k).stem for k in keys]

    if not previous:
        return
    if not any(changes.values()):
        print(f"  unchanged since {previous.get('fetched', 'the last fetch')[:10]}")
        return
    since = previous.get("fetched", "?")[:10]
    print(f"  changes since {since}:")
    for kind in ("added", "changed", "removed"):
        items = names(changes[kind])
        if not items:
            continue
        shown = ", ".join(items[:limit])
        more = f" … and {len(items) - limit} more" if len(items) > limit else ""
        print(f"    {kind:8} {len(items):3}  {shown}{more}")


# --- fetching -----------------------------------------------------------------

def _sparse_clone(target: Path) -> None:
    subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", "--depth", "1",
                    URL, str(target)], check=True, capture_output=True, text=True)
    for cmd in (["sparse-checkout", "init", "--cone"],
                ["sparse-checkout", "set", SUBDIR],
                ["checkout"]):
        subprocess.run(["git", "-C", str(target)] + cmd,
                       check=True, capture_output=True, text=True)


def _git_update(target: Path) -> bool:
    """Fast-forward an existing checkout. False if that was not possible."""
    r = subprocess.run(["git", "-C", str(target), "pull", "--ff-only", "--depth", "1"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ! could not update the checkout ({r.stderr.strip().splitlines()[-1:] or ['']}[0])")
        return False
    return True


def _api_sync(target: Path, known: dict[str, str]) -> None:
    """Fetch over the GitHub API, downloading only files whose blob hash differs
    from what is already on disk. Used when git cannot do a partial clone."""
    owner_repo = URL.removeprefix("https://github.com/").removesuffix(".git")
    with urllib.request.urlopen(
            f"https://api.github.com/repos/{owner_repo}/git/trees/HEAD?recursive=1",
            timeout=60) as fh:
        tree = json.load(fh)
    if tree.get("truncated"):
        print("  ! GitHub truncated the file listing; the fetch may be incomplete")
    upstream = {e["path"]: e["sha"] for e in tree.get("tree", [])
                if e["type"] == "blob" and e["path"].startswith(SUBDIR + "/")
                and e["path"].endswith(".xml")}

    stale = [p for p, sha in upstream.items() if known.get(p) != sha]
    for p in set(known) - set(upstream):          # deleted upstream
        (target / p).unlink(missing_ok=True)
    print(f"  {len(stale)} of {len(upstream)} files to download")
    for i, rel in enumerate(stale, 1):
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(
                f"https://raw.githubusercontent.com/{owner_repo}/HEAD/{rel}", timeout=60) as fh:
            dest.write_bytes(fh.read())
        if i % 100 == 0:
            print(f"  {i}/{len(stale)}")


def _size(path: Path) -> str:
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return f"{total / 1024 / 1024:.1f} MB"


def fetch(target: Path, manifest_path: Path, root: Path) -> dict:
    """Bring ``target`` up to date with upstream and rewrite the manifest."""
    previous = read_manifest(manifest_path)
    fresh = not has_editions(target)

    if fresh:
        print(f"fetching {SUBDIR}/ from {URL} -> {target.relative_to(root)}")
        target.mkdir(parents=True, exist_ok=True)
        try:
            _sparse_clone(target)
        except (OSError, subprocess.CalledProcessError) as exc:
            detail = str(getattr(exc, "stderr", "") or exc).strip()[:120]
            print(f"  sparse clone unavailable ({detail}); using the GitHub API")
            _api_sync(target, {})
    else:
        print(f"updating {target.relative_to(root)}")
        if (target / ".git").is_dir():
            _git_update(target)
        else:
            _api_sync(target, (previous or {}).get("files") or {})

    files = scan(target)
    changes = diff(previous, files)
    manifest = write_manifest(manifest_path, target, files, root)
    print(f"  {manifest['edition_count']} editions, {_size(target)}"
          + (f", commit {manifest['commit'][:7]} ({manifest.get('commit_date', '')[:10]})"
             if manifest.get("commit") else ""))
    report(changes, previous)
    print(f"  -> wrote {manifest_path.relative_to(root)}")
    return manifest


def count_editions(target: Path) -> int:
    return sum(1 for p in target.rglob("*.xml")
               if ".git" not in p.parts and OGHAM_ID_RE.fullmatch(p.stem))


def provenance(manifest_path: Path, corpus_dir: Path) -> dict:
    """Provenance of the corpus **that was actually read**.

    Read from the checkout itself, not from the manifest: the manifest describes
    ``data/origin/``, and stamping its commit onto a graph built from some other
    directory would be a false provenance claim -- worse than none.
    """
    head = git_head(corpus_dir)
    if head:
        remote = git_remote(corpus_dir) or URL
        out = {"source": remote, "edition_count": count_editions(corpus_dir), **head}
        if "github.com" in remote:
            web = remote.removesuffix(".git")
            out["tree_url"] = f"{web}/tree/{head['commit']}/{SUBDIR}"
        m = read_manifest(manifest_path)
        if m.get("commit") == head["commit"] and m.get("fetched"):
            out["fetched"] = m["fetched"]
        return out

    m = read_manifest(manifest_path)
    if m and _same_checkout(m, corpus_dir, manifest_path):
        out = {k: m[k] for k in ("source", "fetched", "commit", "commit_date",
                                 "edition_count") if k in m}
        if m.get("commit"):
            out["tree_url"] = f"{WEB}/tree/{m['commit']}/{SUBDIR}"
        return out
    return {}


def _same_checkout(manifest: dict, corpus_dir: Path, manifest_path: Path) -> bool:
    """True if the manifest describes this very directory."""
    recorded = manifest.get("checkout")
    if not recorded:
        return False
    root = manifest_path.parent.parent          # data/<file>.yaml -> repo root
    try:
        return (root / recorded).resolve() == corpus_dir.resolve()
    except OSError:
        return False
