from app import precreate_demo_repos
import sys


if len(sys.argv) != 2
    n = sys.argv[1]
    if isinstance(n, int) and n > 0:
        precreate_demo_repos(n)
        print("Successfully precreated repos!")
    else:
        print("Argument must be integer greater than 0!")
else:
    print("Please enter the number of repos to precreate.")