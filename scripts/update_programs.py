"""Update usgsprograms.toml targets to the latest GitHub release."""

import argparse
import re
import textwrap
from pathlib import Path

# tomllib is in the standard library from python 3.11, and tomli is the same
# reader for python 3.10, which is still supported
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from pymake.utils.download import get_repo_assets, repo_latest_version

_epilog = """\
Report the latest GitHub release for each target in usgsprograms.toml that is
downloaded from a GitHub repository, and optionally update the target to that
release. Targets that are not downloaded from GitHub, and targets downloaded
from a branch archive, are skipped. Use --apply to rewrite usgsprograms.toml.
"""
_project_root_path = Path(__file__).parent.parent
_programs_path = _project_root_path / "pymake" / "utils" / "usgsprograms.toml"

# the field order written for each target
_columns = (
    "target",
    "version",
    "current",
    "url",
    "dirname",
    "srcdir",
    "standard_precision",
    "double_precision",
    "shared_object",
)

# a release asset url, for example
# https://github.com/MODFLOW-ORG/triangle/releases/download/v1.6/triangle_source.zip
_asset_url = re.compile(
    r"^https://github\.com/(?P<repo>[^/]+/[^/]+)/releases/download/(?P<tag>[^/]+)/(?P<asset>.+)$"
)

# a tag archive url, for example
# https://github.com/MODFLOW-ORG/mt3d-usgs/archive/refs/tags/v1.1.1.zip
_tag_url = re.compile(
    r"^https://github\.com/(?P<repo>[^/]+/[^/]+)/archive/refs/tags/(?P<tag>.+)\.zip$"
)

# a branch archive url, which has no release to track
_branch_url = re.compile(
    r"^https://github\.com/(?P<repo>[^/]+/[^/]+)/archive/refs/heads/(?P<branch>.+)\.zip$"
)


def archive_dirname(repo, tag):
    """Get the directory a GitHub tag archive extracts into.

    GitHub removes a leading 'v' or 'V' from the tag only when it is followed
    by a digit, so the tag 'v1.6' gives '<name>-1.6' but the tag 'v.1.12.00'
    gives '<name>-v.1.12.00'.

    Parameters
    ----------
    repo : str
        GitHub repository, for example 'MODFLOW-ORG/triangle'
    tag : str
        release tag

    Returns
    -------
    dirname : str
        directory the tag archive extracts into

    """
    name = repo.split("/")[-1]
    return f"{name}-{re.sub(r'^[vV](?=[0-9])', '', tag)}"


def version_from_tag(tag):
    """Get a version number from a release tag.

    Parameters
    ----------
    tag : str
        release tag, for example 'v1.6', 'V2.6.2', or 'v.1.12.00'

    Returns
    -------
    version : str
        version number with any leading 'v' or 'V' removed

    """
    return re.sub(r"^[vV]\.?", "", tag)


def parse_programs(path):
    """Read usgsprograms.toml into the leading comments and a list of targets.

    Parameters
    ----------
    path : Path
        path to usgsprograms.toml

    Returns
    -------
    header : str
        the comments the file opens with
    rows : list
        list of dictionaries keyed on the field names

    """
    text = path.read_text()
    with open(path, "rb") as f:
        programs = tomllib.load(f)["program"]

    # the comments the file opens with are kept, so a note added by hand is
    # not lost when the file is written back
    header = text[: text.index("[program.")]
    rows = [{"target": target, **entry} for target, entry in programs.items()]

    return header, rows


def format_programs(header, rows):
    """Format the header and rows as usgsprograms.toml content.

    Parameters
    ----------
    header : str
        the comments the file opens with
    rows : list
        list of dictionaries keyed on the field names

    Returns
    -------
    content : str
        usgsprograms.toml content

    """
    lines = [header.rstrip("\n"), ""]
    for row in rows:
        # a target name may contain a dot, which is a table separator
        lines.append(f'[program."{row["target"]}"]')
        for name in _columns[1:]:
            value = row[name]
            if isinstance(value, bool):
                lines.append(f"{name} = {str(value).lower()}")
            else:
                lines.append(f'{name} = "{value}"')
        lines.append("")

    # the file ends with a single newline after the last field
    return "\n".join(lines)


def _substitute_tag(value, tag, latest):
    """Substitute a release tag, or the version in it, into a value.

    Parameters
    ----------
    value : str
        value that may embed the tag or the version, for example an asset
        name or an extracted directory name
    tag : str
        the release tag being replaced
    latest : str
        the release tag replacing it

    Returns
    -------
    value : str
        value with the tag or version substituted

    """
    for old, new in ((tag, latest), (version_from_tag(tag), version_from_tag(latest))):
        if old in value:
            return value.replace(old, new)

    return value


def _resolve_asset(row, match, latest, verbose=False):
    """Determine the release asset url and directory for a target.

    Parameters
    ----------
    row : dict
        a usgsprograms.toml row
    match : re.Match
        the match of the row url against the release asset pattern
    latest : str
        the latest release tag
    verbose : bool
        boolean indicating if output will be printed to the terminal

    Returns
    -------
    status : str
        a terminal status, or None when the url was resolved
    detail : str
        description of the status
    update : dict
        column values to change

    """
    repo, tag, asset = match.group("repo"), match.group("tag"), match.group("asset")

    try:
        assets = get_repo_assets(github_repo=repo, version=latest)
    except Exception as exc:
        return "error", f"{repo} {latest} assets: {type(exc).__name__}", {}

    # the asset name often embeds the tag or version, so substitute both, then
    # confirm the asset is actually in the release before using it
    candidates = (_substitute_tag(asset, tag, latest), asset)
    new_asset = next((name for name in candidates if name in assets), None)
    if new_asset is None:
        return (
            "manual",
            f"{repo} {tag} -> {latest}, no asset matching '{asset}' "
            f"(release has: {', '.join(sorted(assets))})",
            {},
        )

    if new_asset != asset and verbose:
        print(f"    asset {asset} -> {new_asset}")

    # the extracted directory often embeds the tag or version, for example
    # 'mf6.6.3_linux'. a directory that embeds neither, such as '.', is
    # left alone
    update = {"url": assets[new_asset]}
    dirname = _substitute_tag(row["dirname"], tag, latest)
    if dirname != row["dirname"]:
        update["dirname"] = dirname

    return None, "", update


def resolve_target(row, verbose=False):
    """Determine the latest release for a target.

    Parameters
    ----------
    row : dict
        a usgsprograms.toml row
    verbose : bool
        boolean indicating if output will be printed to the terminal

    Returns
    -------
    status : str
        one of 'current', 'update', 'manual', 'skipped', or 'error'
    detail : str
        description of the status
    update : dict
        column values to change, empty if there is nothing to change

    """
    url = row["url"]
    asset_match = _asset_url.match(url)
    tag_match = _tag_url.match(url)

    if _branch_url.match(url):
        return "skipped", "branch archive, no release to track", {}
    if asset_match is None and tag_match is None:
        return "skipped", "not downloaded from GitHub", {}

    match = asset_match or tag_match
    repo, tag = match.group("repo"), match.group("tag")

    try:
        latest = repo_latest_version(github_repo=repo)
    except Exception as exc:
        return "error", f"{repo}: {type(exc).__name__}", {}

    if latest == tag:
        return "current", f"{repo} {tag}", {}

    update = {}
    if tag_match is not None:
        update["url"] = url.replace(f"/tags/{tag}.zip", f"/tags/{latest}.zip")
        update["dirname"] = archive_dirname(repo, latest)
    else:
        status, detail, asset_update = _resolve_asset(row, match, latest, verbose)
        if status is not None:
            return status, detail, {}
        update.update(asset_update)

    # only update the version when the current one was derived from the old tag
    if row["version"] == version_from_tag(tag):
        update["version"] = version_from_tag(latest)
        detail = f"{repo} {tag} -> {latest}"
    else:
        detail = (
            f"{repo} {tag} -> {latest} (version '{row['version']}' does not match "
            f"tag '{tag}', left unchanged)"
        )

    return "update", detail, update


def main():
    """Report and optionally apply GitHub release updates."""
    parser = argparse.ArgumentParser(
        prog="update_programs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(_epilog),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="rewrite usgsprograms.toml with the latest releases",
    )
    parser.add_argument(
        "-t",
        "--target",
        action="append",
        help="only consider the named target, can be repeated",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print additional information to the terminal",
    )
    args = parser.parse_args()

    header, rows = parse_programs(_programs_path)

    updates = 0
    for row in rows:
        if args.target and row["target"] not in args.target:
            continue
        status, detail, update = resolve_target(row, verbose=args.verbose)
        if status == "skipped" and not args.verbose:
            continue
        print(f"  {row['target']:<11s} {status:<8s} {detail}")
        if update:
            updates += 1
            for name, value in update.items():
                print(f"    {name}: {row[name]} -> {value}")
            row.update(update)

    if updates == 0:
        print("\nno updates available")
        return

    if args.apply:
        _programs_path.write_text(format_programs(header, rows))
        print(f"\nupdated {updates} target(s) in {_programs_path}")
    else:
        print(f"\n{updates} update(s) available, re-run with --apply to write them")


if __name__ == "__main__":
    main()
