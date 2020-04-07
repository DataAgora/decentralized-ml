import sys
import os

from notebook.auth.security import set_password


set_password(password=sys.argv[1])
