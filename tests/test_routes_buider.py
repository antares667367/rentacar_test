import pytest

from src import RBuilder

RB = RBuilder.builder("/base")


def test_all_is_str():
    assert RBuilder.strings.is_all_strings(["a", "a", "b"])
    with pytest.raises(RBuilder.errors.wrongType):
        RBuilder.strings.is_all_strings(["a", "a", 1])


@pytest.mark.parametrize(
    "input,error",
    [
        (b"xxxx", RBuilder.errors.wrongType),
        ([], RBuilder.errors.wrongType),
        (1, RBuilder.errors.wrongType),
        (1.1, RBuilder.errors.wrongType),
        (False, RBuilder.errors.wrongType),
    ],
)
def test_is_string(input, error):
    """Test if input is a string .

    Args:
        input (any): something to be tested
        error (RouteBuilderError): the expected error
    """
    with pytest.raises(error):
        RBuilder.strings.is_string(input)


def test_builder():
    """Test builder."""
    # test building a base route
    RB.add_path("yolo", "yolo")
    yolo = RB.path("yolo")
    assert yolo == "/base/yolo"
