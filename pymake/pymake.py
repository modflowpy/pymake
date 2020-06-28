from .pymake_base import parser
from .build_program import build_apps


class Pymake:
    def __init__(self, name="pymake"):
        self.name = name

    def get_parser(self):
        return parser()

    def build(self, targets="mf6"):
        """

        Parameters
        ----------
        targets

        Returns
        -------

        """
        returncode = build_apps(targets=targets)
        if isinstance(targets, str):
            targets = [targets]
        if returncode != 0:
            raise FileNotFoundError(
                "could not build {}".format(" ".join(targets))
            )
        return returncode
