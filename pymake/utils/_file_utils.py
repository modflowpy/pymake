import os


def _get_extra_exclude_files(external_file):
    """Get files to include or exclude in compilation from an external
    file or a list.

    Parameters
    ----------
    external_file : str or list
        path for extrafiles file that contains paths to additional source
        files to include

    Returns
    -------
    files : list
        list of files in the external file or list

    """
    if external_file is None:
        files = None
    else:
        if isinstance(external_file, (list, tuple)):
            files = external_file
        elif os.path.isfile(external_file):
            efpth = os.path.dirname(external_file)
            with open(external_file, "r") as f:
                files = []
                for line in f:
                    fname = line.strip().replace("\\", "/")
                    if len(fname) > 0:
                        fname = os.path.abspath(os.path.join(efpth, fname))
                        files.append(fname)
        else:
            raise Exception(
                "extrafiles must be either a list of files "
                "or the name of a text file that contains a list "
                "of files."
            )
    return files


def _get_extrafiles_common_path(external_files):
    """

    Parameters
    ----------
    external_file : str or list
        path for extrafiles file that contains paths to additional source
        files to include

    Returns
    -------
    common_path : str
        common path for files in external_file

    """
    if external_files is None:
        common_path = None
    else:
        common_path = os.path.commonpath(
            _get_extra_exclude_files(external_files)
        )
        for tag in (f"src{os.sep}", f"source{os.sep}"):
            if tag in common_path:
                str_index = common_path.find(tag)
                if str_index >= 0:
                    common_path = common_path[0 : str_index + len(tag)]
                break
    return common_path
