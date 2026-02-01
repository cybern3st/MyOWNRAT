import argparse
from interface import INTERFACE
from parser import PARSER


def build_parser():
    parser = argparse.ArgumentParser(
        description="MyOWNRAT server",
        add_help=False
    )

    parser.add_argument(
        "mode",
        nargs="?",
        help="Operation to perform (bind)"
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        dest="help",
        help="Show help for the selected mode"
    )
    parser.add_argument(
        "-a",
        "--address",
        default="127.0.0.1",
        help="Address to bind"
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Port to bind"
    )
    parser.add_argument(
        "--ssl",
        action="store_true",
        default=True,
        help="Enable SSL/TLS (default: enabled)"
    )
    parser.add_argument(
        "--no-ssl",
        action="store_false",
        dest="ssl",
        help="Disable SSL/TLS (not recommended for production)"
    )

    return parser


def main():
    args = build_parser().parse_args()
    parsed = PARSER(args)

    if parsed.mode == "bind":
        interface = INTERFACE(parsed)
        interface.bind()
        interface.accept()
        try:
            interface.launch()
        finally:
            # close() in INTERFACE è alias di stop()
            interface.close()

if __name__ == "__main__":
    main()
