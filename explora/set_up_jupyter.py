import sys
import os

from notebook.auth.security import set_password

if sys.argv[1] == sys.argv[2]:
    os.remove("Explora.ipynb")
    os.remove("ExploraMobileText.ipynb")
