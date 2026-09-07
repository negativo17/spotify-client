#!/usr/bin/python3
"""Update the spotify-client package to the latest upstream release.

Queries the Spotify origin repository for the newest amd64 .deb, and if it is
newer than the version currently in the spec file: bumps the spec, downloads
the .deb, repacks its payload into the tarball referenced by Source0 and
commits the result.
"""

import argparse
import functools
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import rpm

NAME = "spotify-client"
SPEC = f"{NAME}.spec"
REPO = "https://repository-origin.spotify.com/pool/non-free/s/spotify-client/"

# Upstream publishes one .deb per architecture; we only ship x86_64.
DEB_RE = re.compile(rf'href="{re.escape(NAME)}_([^"/]+)_amd64\.deb"')


def run(*cmd, **kwargs):
    """Run a command, echoing it first, and abort on failure."""
    print("+", " ".join(str(c) for c in cmd), file=sys.stderr)
    return subprocess.run(cmd, check=True, **kwargs)


def evr(version):
    """Split an upstream version into an rpm (epoch, version, release) tuple."""
    ver, _, rel = version.partition("-")
    return ("0", ver, rel or "0")


def newer(a, b):
    """True if version a is strictly newer than version b."""
    return rpm.labelCompare(evr(a), evr(b)) > 0


def available_versions():
    """Return every amd64 version offered by the repository, newest last."""
    try:
        with urllib.request.urlopen(REPO, timeout=60) as response:
            listing = response.read().decode("utf-8", "replace")
    except OSError as error:
        sys.exit(f"error: cannot read {REPO}: {error}")

    versions = sorted(
        set(DEB_RE.findall(listing)),
        key=functools.cmp_to_key(lambda a, b: rpm.labelCompare(evr(a), evr(b))),
    )
    if not versions:
        sys.exit(f"error: no {NAME}_*_amd64.deb found at {REPO}")
    return versions


def spec_version():
    """Return the Version: currently declared in the spec file."""
    match = re.search(r"^Version:\s*(\S+)", Path(SPEC).read_text(), re.M)
    if not match:
        sys.exit(f"error: no Version: tag found in {SPEC}")
    return match.group(1)


def download(version):
    """Fetch the .deb for the given version, resuming a partial download."""
    deb = f"{NAME}_{version}_amd64.deb"
    run("wget", "-c", "-O", deb, f"{REPO}{deb}")
    return Path(deb)


def unpack(deb, version):
    """Unpack the .deb payload into the source directory expected by the spec."""
    srcdir = Path(f"{NAME}-{version}")
    temp = Path("temp")

    shutil.rmtree(temp, ignore_errors=True)
    shutil.rmtree(srcdir, ignore_errors=True)
    temp.mkdir()

    # "ar x" extracts into the current directory, so unpack inside temp/.
    run("ar", "x", os.path.relpath(deb, temp), cwd=temp)

    # Upstream has used gz and zst over time; let tar detect the compression.
    data = next((p for p in temp.glob("data.tar*")), None)
    if data is None:
        sys.exit(f"error: no data.tar.* member inside {deb}")
    run("tar", "-xf", data.name, cwd=temp)

    payload = temp / "usr/share/spotify"
    if not payload.is_dir():
        sys.exit(f"error: {deb} does not contain usr/share/spotify")
    payload.rename(srcdir)
    shutil.rmtree(temp, ignore_errors=True)
    return srcdir


def make_tarball(srcdir, version):
    """Compress the unpacked payload into the Source0 tarball."""
    tarball = Path(f"{NAME}-{version}.tar.xz")
    tarball.unlink(missing_ok=True)

    # xz is single-threaded by default and this payload is ~170 MB.
    env = dict(os.environ)
    env.setdefault("XZ_OPT", "-T0")
    run("tar", "-cJf", tarball, "--remove-files", srcdir, env=env)
    return tarball


def prune(keep):
    """Drop superseded .deb files and tarballs; they are all git-ignored."""
    for stale in [*Path().glob(f"{NAME}*.deb"), *Path().glob(f"{NAME}-*.tar.xz")]:
        if stale != keep:
            print(f"removing superseded {stale}", file=sys.stderr)
            stale.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version",
        nargs="?",
        help="version to update to (default: the newest one upstream)",
    )
    parser.add_argument(
        "-l", "--list", action="store_true", help="list upstream versions and exit"
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="rebuild even if the spec is already at that version",
    )
    parser.add_argument(
        "-n", "--no-commit", action="store_true", help="leave the changes uncommitted"
    )
    parser.add_argument(
        "-k", "--keep-deb", action="store_true", help="keep the downloaded .deb"
    )
    args = parser.parse_args()

    # Always operate on the package directory, whatever the caller's cwd is.
    os.chdir(Path(__file__).resolve().parent)

    if args.list:
        for version in available_versions():
            print(version)
        return

    version = args.version or available_versions()[-1]
    current = spec_version()

    if not args.force:
        if version == current:
            print(f"{NAME} is already at {current}, nothing to do")
            return
        if not newer(version, current):
            sys.exit(
                f"error: {version} is older than the packaged {current} "
                f"(use --force to downgrade)"
            )

    print(f"updating {NAME} from {current} to {version}")
    run("rpmdev-bumpspec", "-D", "-c", f"Update to {version}.", "-n", version, SPEC)

    deb = download(version)
    tarball = make_tarball(unpack(deb, version), version)
    if not args.keep_deb:
        deb.unlink(missing_ok=True)
    prune(keep=tarball)

    if args.no_commit:
        print(f"created {tarball}; spec bumped but not committed")
        return

    run("git", "commit", "-a", "-m", f"Update to {version}")


if __name__ == "__main__":
    main()
