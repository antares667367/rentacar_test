from .tools.arguments import rentacar_args
from .tools.dbutils import pass_auth
from .tools.routes_builders import (
    RoutesBuilder,
    RoutesBuilderWrongType,
    is_all_strings,
    is_string,
)


class RbuilderStrings:
    """strings methods rbuilder ."""

    is_string = is_string
    is_all_strings = is_all_strings


class RbuilderErrors:
    """RbuilerErrors"""

    wrongType = RoutesBuilderWrongType


class RBuilder:
    errors = RbuilderErrors
    strings = RbuilderStrings
    builder = RoutesBuilder
