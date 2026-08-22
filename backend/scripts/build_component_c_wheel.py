#!/usr/bin/env python3
"""R0-a — the committed, runnable build invocation for the Component C wheel.

WHY THIS SCRIPT EXISTS. `provenance/component-c-live-engine-manifest.json`'s
`package.build_command` documents the INNER command
(`python -m build --wheel --no-isolation --outdir <dist>`, with pinned
setuptools/wheel/build versions, run inside the exact application base image) and
`buildLog1.md`'s "Real build." paragraph (2026-08-15 entry, "Component C Phase 1 batch 1a")
describes the OUTER `docker run` wrapper in prose: the packaging tree bind-mounted read-only at
`/src`, copied to a writable `/build_src` inside the container so `python -m build`'s own
`build/`/`*.egg-info/` artefacts never touch the host, and `--outdir` pointed at a bind-mounted
`/dist`. Until this script, that wrapper existed only as prose and had to be reconstructed by
hand for every rebuild. This is that wrapper, committed and runnable.

WHAT THIS SCRIPT DOES NOT DO. It never writes into `backend/provenance/wheels/` — that directory
holds the committed, hash-pinned artefacts the provenance chain rests on, and this script refuses
to build into it or anywhere else inside the repository. `--outdir` must resolve outside this
checkout; the script exits before invoking Docker if it does not. It never records an approval,
threshold, or checksum decision, and it never overwrites `component-c-live-engine-manifest.json`.
A rebuild's sha256 either matches the committed wheel's or it does not; either outcome is a
finding to write down, not something for this script to adjudicate or paper over.

USAGE (from `backend/`, or anywhere — paths below are absolute):
    python scripts/build_component_c_wheel.py --outdir /path/outside/the/repo

Then compare the printed sha256 against `package.wheel_sha256` in
`provenance/component-c-live-engine-manifest.json` (currently
`62b85a051733b00f16791a04c019a229924bbae0144de3441c27666eff3c3b39` for
`prabathi_component_c_live_engine-0.1.0+c2.09267ab-py3-none-any.whl`). This script prints that
comparison itself; nothing extra needs to be typed.

HOW `requirements.lock` IS REGENERATED (documented here because this is the file that would
otherwise document it and doesn't): NOT via `pip-compile`. `pip-compile` (or any other lockfile
generator) appears nowhere in this repository — no config for it, no invocation of it in any
script, README, or build log entry. Every wheel re-pin to date (see `buildLog1.md`, and
`git show ce00274 -- requirements.lock`) has instead hand-edited exactly the two-line
`./provenance/wheels/<filename>.whl` + `--hash=sha256:<value>` block for the wheel(s) that moved,
leaving the rest of the file (all PyPI-sourced pins and their hash sets) untouched. That commit's
diff to `requirements.lock` is 4 insertions / 4 deletions across the whole file — the two
path+hash pairs for B and C, nothing else — which is the direct evidence this is a hand edit, not
a tool regenerating the file (a `pip-compile` run touches comment headers, ordering, and often
transitive hash sets even when only one line's content actually changes). This is not a defect
this script fixes; it is a manual step this script simply refuses to leave undocumented. If a
future rebuild changes `requirements.lock`, the two-line block for the wheel(s) that moved is
edited by hand, and the new wheel's real sha256 (as printed by this script, or by
`sha256sum`/`Get-FileHash`) is what goes into the `--hash=sha256:` line — never a value invented
or carried over from a previous version.

Governed by `Component_C_9b_9c_And_Generator_Plan_v1.0.md`'s R0-a. Batch scope: packaging/build
tooling only. No wheel produced by this script is ever copied into `backend/provenance/wheels/`
by this script itself — that copy, if ever wanted, is a separate, deliberate, human action.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

# backend/scripts/build_component_c_wheel.py -> backend/ -> repo root
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent
REPO_ROOT = BACKEND_DIR.parent

PACKAGING_SRC = BACKEND_DIR / "packaging" / "component_c_internal"
WHEELS_DIR = BACKEND_DIR / "provenance" / "wheels"

# Exact application base image, by digest — not a merely-compatible local interpreter. Matches
# backend/Dockerfile's FROM line and provenance/component-c-live-engine-manifest.json's
# package.build_command field.
BASE_IMAGE = (
    "docker.io/library/python:3.11.15-slim-bookworm"
    "@sha256:b18992999dbe963a45a8a4da40ac2b1975be1a776d939d098c647482bcad5cba"
)

# Exact build tooling versions, matching package.build_command in the C manifest.
SETUPTOOLS_VERSION = "setuptools==80.10.2"
WHEEL_VERSION = "wheel==0.46.3"
BUILD_VERSION = "build==1.2.2.post1"

# The currently-committed wheel, for the byte-identity comparison this script prints.
COMMITTED_WHEEL_FILENAME = "prabathi_component_c_live_engine-0.1.0+c2.09267ab-py3-none-any.whl"
COMMITTED_WHEEL_SHA256 = "62b85a051733b00f16791a04c019a229924bbae0144de3441c27666eff3c3b39"


def fatal(message: str) -> "None":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def _resolve_and_guard_outdir(raw_outdir: Path) -> Path:
    """Refuse any --outdir that resolves inside this repository checkout, including
    backend/provenance/wheels/ itself. This is the one hard rule this script will not bend on:
    build artefacts from a reproducibility experiment must never land where the committed,
    hash-pinned wheel lives, even by accident (e.g. a relative path typo)."""
    outdir = raw_outdir.expanduser().resolve()
    guarded_roots = (REPO_ROOT, BACKEND_DIR, WHEELS_DIR)
    for guarded in guarded_roots:
        guarded_resolved = guarded.resolve()
        if outdir == guarded_resolved or guarded_resolved in outdir.parents:
            fatal(
                f"--outdir ({outdir}) resolves inside the repository checkout "
                f"({guarded_resolved}). This script refuses to write build output anywhere in "
                f"the repo, and especially never into backend/provenance/wheels/ -- pass a "
                f"scratch directory outside the checkout entirely."
            )
    return outdir


def _find_produced_wheel(outdir: Path) -> Path:
    candidates = sorted(outdir.glob("prabathi_component_c_live_engine-*.whl"))
    if not candidates:
        fatal(f"no prabathi_component_c_live_engine-*.whl found in {outdir} after the build")
    if len(candidates) > 1:
        print(
            f"WARNING: {len(candidates)} candidate wheels found in {outdir}; "
            f"using the most recently modified one.",
            file=sys.stderr,
        )
        candidates.sort(key=lambda p: p.stat().st_mtime)
    return candidates[-1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild the Component C wheel inside the exact pinned base image, reproducing the "
            "docker run wrapper documented only in prose until now (buildLog1.md's 'Real build.' "
            "paragraph). Output goes to --outdir, which must be OUTSIDE this repository."
        )
    )
    parser.add_argument(
        "--outdir",
        required=True,
        type=Path,
        help=(
            "Scratch directory for the built wheel. Must resolve outside this repository "
            "checkout (refused otherwise). Never backend/provenance/wheels/."
        ),
    )
    parser.add_argument(
        "--docker-bin",
        default="docker",
        help="Docker executable to invoke (default: docker).",
    )
    args = parser.parse_args()

    if not PACKAGING_SRC.is_dir():
        fatal(
            f"{PACKAGING_SRC} not found. This script must be run against a full checkout that "
            f"includes backend/packaging/component_c_internal/ (excluded from the application "
            f"Docker image by .dockerignore, but present in a normal host checkout)."
        )

    outdir = _resolve_and_guard_outdir(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # The inner build command, run inside the container. Mirrors package.build_command exactly:
    # copy the read-only /src mount to a writable /build_src first, so python -m build's own
    # build/ and *.egg-info/ artefacts never touch the read-only source (and, since /src is a
    # bind mount of the host's packaging tree, never touch the host checkout either) -- only the
    # finished .whl crosses back out, via the /dist bind mount.
    inner_command = (
        "set -eu; "
        "cp -r /src /build_src && "
        "cd /build_src && "
        f"pip install --quiet {SETUPTOOLS_VERSION} {WHEEL_VERSION} {BUILD_VERSION} && "
        "python -m build --wheel --no-isolation --outdir /dist"
    )

    docker_command = [
        args.docker_bin,
        "run",
        "--rm",
        "-v",
        f"{PACKAGING_SRC}:/src:ro",
        "-v",
        f"{outdir}:/dist",
        BASE_IMAGE,
        "bash",
        "-c",
        inner_command,
    ]

    print("Building Component C wheel.")
    print(f"  base image : {BASE_IMAGE}")
    print(f"  source     : {PACKAGING_SRC} (read-only mount)")
    print(f"  outdir     : {outdir}")
    print(f"  command    : {' '.join(docker_command)}")
    print()

    result = subprocess.run(docker_command)
    if result.returncode != 0:
        fatal(f"docker run exited {result.returncode}; see output above")

    produced_wheel = _find_produced_wheel(outdir)
    produced_sha256 = hashlib.sha256(produced_wheel.read_bytes()).hexdigest()

    print()
    print(f"Produced wheel : {produced_wheel}")
    print(f"Produced sha256: {produced_sha256}")
    print(f"Committed wheel: {WHEELS_DIR / COMMITTED_WHEEL_FILENAME}")
    print(f"Committed sha256: {COMMITTED_WHEEL_SHA256}")
    print()

    if produced_wheel.name == COMMITTED_WHEEL_FILENAME and produced_sha256 == COMMITTED_WHEEL_SHA256:
        print("REPRODUCIBLE: byte-identical to the committed wheel.")
    elif produced_wheel.name != COMMITTED_WHEEL_FILENAME:
        print(
            "NOTE: produced wheel filename differs from the currently-committed wheel filename "
            "(expected if pyproject.toml's version has moved since the committed wheel was "
            "built). Compare produced_sha256 above against the sha256 recorded for whichever "
            "version this checkout's pyproject.toml declares."
        )
    else:
        print(
            "NOT BYTE-IDENTICAL: sha256 differs from the committed wheel. This is a finding to "
            "record, not to fix by editing any recorded checksum or by replacing the committed "
            "wheel. The usual cause is zip entry timestamps / file-order nondeterminism in "
            "python -m build's own wheel writer; SOURCE_DATE_EPOCH (and, if that alone is "
            "insufficient, a deterministic re-zip pass) is the standard remedy to investigate, "
            "not applied automatically by this script."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
