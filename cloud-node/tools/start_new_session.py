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

    model_path = "../tests/artifacts/{}"
    if library == 'ios':
        h5_model_path = model_path.format("ios_model.h5")
        loop.run_until_complete(explora.start_new_session(repo_id, "IOS", h5_model_path))
    elif library == 'python':
        h5_model_path = model_path.format("my_model.h5")
        loop.run_until_complete(explora.start_new_session(repo_id, "PYTHON", h5_model_path))
    else:
        print("Library not supported!")