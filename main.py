import sys

from cli.cli import Cli
from core.setup import Filesystem


def main():
	cli = Cli(filesystem=Filesystem())
	return cli.run()


if __name__ == "__main__":
	sys.exit(main())
