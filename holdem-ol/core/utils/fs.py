import os


def list_files_with_prefix(path: str, prefix: str) -> list:
    """
    specify a path and a file prefix,
    then list and sort the files in the directory with the prefix
    """
    files = os.listdir(path)
    files = list(filter(lambda x: x.startswith(prefix), files))
    files.sort()
    return files


def list_files_with_affix(path: str, affix: str) -> list:
    """
    specify a path and a file affix,
    then list and sort the files in the directory with the affix
    """
    files = os.listdir(path)
    files = list(filter(lambda x: x.endswith(affix), files))
    files.sort()
    return files
