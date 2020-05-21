from app import precreate_demo_repos
import sys

print(sys.argv)
if len(sys.argv) == 2:
    try:
        n = int(sys.argv[1])
    except:
        print("Argument must be an integer!")
    

    if n > 0:
        precreate_demo_repos(n)
        print("Successfully precreated repos!")
    else:
        print("Argument must be integer greater than 0!")
    
    
else:
    print("Please enter the number of repos to precreate.")