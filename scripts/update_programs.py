import argparse
import re
import textwrap
from pathlib import Path

from pymake.utils.download import get_repo_assets, repo_latest_version

_epilog = """\
Report the latest GitHub release for each target in usgsprograms.txt that is
downloaded from a GitHub repository, and optionally update the target to that
release. Targets that are not downloaded from GitHub, and targets downloaded
from a branch archive, are skipped. Use --apply to rewrite usgsprograms.txt.
"""
_project_root_path = Path(__file__).parent.parent
_programs_path = _project_root_path / "pymake" / "utils" / "usgsprograms.txt"

# usgsprograms.txt column order
_columns = (
    "target",
    "version",
    "current",
    "url",
    "dirname",
    "srcdir",
    "standard_switch",
    "double_switch",
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
    """Read usgsprograms.txt into a list of dictionaries.

    Parameters
    ----------
    path : Path
        path to usgsprograms.txt

    Returns
    -------
    header : str
        the header line
    rows : list
        list of dictionaries keyed on the column names

    """
    lines = path.read_text().splitlines()
    header, rows = lines[0], []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = [value.strip() for value in line.split(",")]
        rows.append(dict(zip(_columns, values)))

    return header, rows


def format_programs(header, rows):
    """Format the header and rows as aligned usgsprograms.txt content.

    Column widths are taken from the header so that an updated file keeps the
    alignment of the original.

    Parameters
    ----------
    header : str
        the header line
    rows : list
        list of dictionaries keyed on the column names

    Returns
    -------
    content : str
        usgsprograms.txt content

    """
    # each column is padded to the width of its header field, keeping the
    # leading spaces the header uses for that column
    fields = header.split(",")
    layout = [(len(f) - len(f.lstrip(" ")), len(f)) for f in fields]

    lines = [header]
    for row in rows:
        values = []
        for idx, name in enumerate(_columns):
            lead, width = layout[idx]
            values.append(" " * lead + row[name].ljust(width - lead))
        lines.append(",".join(values).rstrip())

    return "\n".join(lines) + "\n"


def resolve_target(row, verbose=False):
    """Determine the latest release for a target.

    Parameters
    ----------
    row : dict
        a usgsprograms.txt row
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
        asset = match.group("asset")
        # the asset name often embeds the tag or version, so substitute both,
        # then confirm the asset is actually in the release before using it
        try:
            assets = get_repo_assets(github_repo=repo, version=latest)
        except Exception as exc:
            return "error", f"{repo} {latest} assets: {type(exc).__name__}", {}

        candidates = [
            asset.replace(tag, latest).replace(
                version_from_tag(tag), version_from_tag(latest)
            ),
            asset,
        ]
        new_asset = next((name for name in candidates if name in assets), None)
        if new_asset is None:
            return (
                "manual",
                f"{repo} {tag} -> {latest}, no asset matching '{asset}' "
                f"(release has: {', '.join(sorted(assets))})",
                {},
            )
        update["url"] = assets[new_asset]
        if new_asset != asset and verbose:
            print(f"    asset {asset} -> {new_asset}")

        # the extracted directory often embeds the tag or version, for example
        # 'mf6.6.3_linux'. a directory that embeds neither, such as '.', is
        # left alone
        dirname = row["dirname"]
        for old, new in (
            (tag, latest),
            (version_from_tag(tag), version_from_tag(latest)),
        ):
            if old in dirname:
                dirname = dirname.replace(old, new)
                break
        if dirname != row["dirname"]:
            update["dirname"] = dirname

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
        help="rewrite usgsprograms.txt with the latest releases",
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
