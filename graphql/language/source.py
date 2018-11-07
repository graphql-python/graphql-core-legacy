import os

__all__ = ["Source", "FileSource"]

class Source(object):
    __slots__ = "body", "name"

    def __init__(self, body, name="GraphQL"):
        # type: (str, str) -> None
        self.body = body
        self.name = name

    def __eq__(self, other):
        return self is other or (
            isinstance(other, Source)
            and self.body == other.body
            and self.name == other.name
        )

class FileSource(Source):
    __slots__ = "body", "name"

    def __init__(self, *args, **kwargs):
        """Create a Source using the specified GraphQL files' contents."""
        name = kwargs.get("name", "GraphQL")

        # From the specified list of paths, first identify all files. Then, load
        # their contents into a single, newline delimited string.
        file_contents = []
        file_paths = self.__get_file_paths__(args)
        for fp in file_paths:
            with open(fp) as f:
                file_contents.append(f.read())
        body = '\n'.join(file_contents)

        super(FileSource, self).__init__(body, name)

    def __get_file_paths__(self, paths):
        """Get the paths to all files in the given list of paths. This means
        filtering out invalid paths and recursively walking a given directory
        path to gather the paths of all files that it contains."""
        all_file_paths = []

        # Filter out invalid paths.
        valid_paths = [p for p in paths if os.path.exists(p)]

        # Add all paths pointing to a file to all_file_paths.
        all_file_paths += [p for p in valid_paths if os.path.isfile(p)]

        # For each path referring to a directory, walk that directory's structure
        # recursively, and add its constituent files' paths to all_file_paths.
        all_file_paths += [
            os.path.join(dir_name, file_name)
            for p in valid_paths
            if os.path.isdir(p)
            for dir_name, _, files_in_dir in os.walk(p)
            for file_name in files_in_dir
        ]

        return all_file_paths
