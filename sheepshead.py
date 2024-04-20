import argparse
import logging.config
import sys

from src.game import play_game

MIN_PY_VERSION = 3, 11
if sys.version_info < MIN_PY_VERSION:
    raise RuntimeError(
        f"Minimum Python version is {MIN_PY_VERSION} but {sys.version_info} was used"
    )

logger = logging.getLogger("sheepshead")


def configure_logging(verbosity):
    levels = [
        # "CRITICAL",
        # "ERROR",
        "WARNING",  # Always log warning
        "INFO",
        "DEBUG",
    ]
    verbosity = min(verbosity, len(levels) - 1)
    level = levels[verbosity]
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": "%(levelname)s: %(message)s"},
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {"root": {"level": f"{level}", "handlers": ["stdout"]}},
    }
    logging.config.dictConfig(logging_config)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="Sheepshead", description="The card game, not the fish"
    )
    parser.add_argument(
        "--hands",
        type=int,
        default=5,
        metavar="#",
        help="Number of hands per game (default: %(default)d)",
    )
    parser.add_argument(
        "-p",
        "--players",
        nargs="+",
        type=str,
        metavar="name",
        help="Opponent names (default: random)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase detail of output messages [-v, -vv, ...]",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-a",
        "--auto",
        action="store_true",
        help="Automatically play a card if it is the only option",
    )
    group.add_argument(
        "-s",
        "--spectate",
        action="store_true",
        help="Run a complete game without user input",
    )
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    configure_logging(args.verbose)
    play_game(args.auto, args.spectate, args.hands, args.players)


if __name__ == "__main__":
    main(sys.argv[1:])
