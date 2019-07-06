import sys

import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.bootstrapper import bootstrap




def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]
    bootstrap()

if __name__ == "__main__":
    main()
