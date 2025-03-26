import os
from typing import Iterable


class RoutesBuilderErrors(Exception):
    """Raised when something goes wrong in the builder"""


class RoutesBuilderWrongType(RoutesBuilderErrors):
    """Raised when the parameter type is not the expected one"""


class RoutesBuilder:
    """Automates boring route path building"""

    def __init__(self, endpoint_base: str) -> None:
        """Initialize the chunk for this endpoint .

        Args:
            endpoint_base (str): The base of the api
        """
        # test path
        is_string(endpoint_base)

        self.chunks = {"base": endpoint_base}
        self.varia = {}

    def add_path(
        self, name: str, path: str, extends: str = None, varia: list = []
    ) -> None:
        """
        Add a new path to the list of routes.

        This method adds a new path to the internal dictionary of routes. It can optionally
        extend an existing path and include variable components.
        Args:
            name (str): The name of the new path, used as the key in the internal dictionary.
            path (str): The path to add.
            extends (str, optional): The name of an existing path to extend. If provided,
            the new path will be appended to this existing path.
            Defaults to None.
            varia (list, optional): A list of variable components for the path. These can be
                                    used to generate multiple variations of the path.
                                    Defaults to an empty list.

        Returns:
            None

        Side effects:
            - Updates self.varia if varia is provided.
            - Updates self.chunks with the new path.
        """
        _ = []
        if varia:
            self.varia[name] = varia
        if extends in self.chunks:
            _.append(self.chunks[extends])
        _.append(path)
        self.chunks[name] = os.path.join(*_)

    def path(self, path_name: str) -> str:
        """Returns the path to the file at the given key.

        Args:
            path_name (str): The name of an existing key

        Returns:
            str: pathlike path
        """
        return os.path.join(self.chunks["base"], self.chunks[path_name])

    def displayroutes(self, trunk=False):
        """Convenient way to display routes"""
        fake = {}
        for k, v in self.chunks.items():
            if k != "base" and (True if trunk else not k.startswith("__")):
                """Base path will not be displayed as an item because
                it's already included
                in the other generated paths.
                Paths with a key starting with __ will
                also not be displayed
                """
                # displayed routes will not include base path
                if k in self.varia:
                    fake[k] = [
                        os.path.join(self.chunks["base"], v.replace("<param>", V))
                        for V in self.varia[k]
                    ]

                else:
                    fake[k] = os.path.join(self.chunks["base"], v)
        return fake


def is_string(value: any) -> None:
    """Validates that value is a string type .

    Args:
        value (any): any value to test

    Raises:
        RoutesBuilderWrongType: Route Builder
    """
    if not isinstance(value, str):
        raise RoutesBuilderWrongType(
            """RouteBuilder accepts only
            str type as key names or key values """
        )
    return True


def is_all_strings(test_list: Iterable) -> bool:
    """Check if all the values in a list are strings .

    Args:
        test_list ([list|tuple]): [a list of values to test]

    Returns:
        [bool]: [a boolean if all expressions in the list is true]
    """
    return all(is_string(x) for x in test_list)
