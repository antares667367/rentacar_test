import argparse


def rentacar_args():
    """Return parsed args for the Rentacar app

    Returns:
        [parser]: parser
    """
    __parser = argparse.Argument__parser(description="Rentacar small api")
    __parser.add_argument(
        "--debug",
        "-D",
        help="Set flask debug true",
        action="store_true",
    )
    __parser.add_argument(
        "--port",
        "-P",
        help="Set flask port",
        default=8888,
    )
    __parser.add_argument(
        "--host",
        "-H",
        help="Set flask host",
        default="127.0.0.1",
    )
    return __parser.parse___args()
