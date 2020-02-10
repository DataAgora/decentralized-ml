import asyncio
import sys

from explora import Explora

libraries = ["ios", "python"]

if len(sys.argv) == 1:
    print("Must include library as argument.")
else:
    library = sys.argv[1]
    loop = asyncio.get_event_loop()
    explora = Explora()
    repo_id = "99885f00eefcd4107572eb62a5cb429a"

    if library == 'ios':
        h5_model_path = "assets/ios_model.h5"
        loop.run_until_complete(explora.start_new_session(repo_id, "IOS", h5_model_path))
    elif library == 'python':
        h5_model_path = "assets/my_model.h5"
        loop.run_until_complete(explora.start_new_session(repo_id, "PYTHON", h5_model_path))
    else:
        print("Library not supported!")