import asyncio
import sys

from explora import Explora

libraries = ["ios", "python"]

if len(sys.argv) != 3:
    print("Must include library as argument.")
else:
    library = sys.argv[1]
    loop = asyncio.get_event_loop()
    explora = Explora()
    repo_id = sys.argv[2]

    model_path = "../tests/artifacts/{}"
    if library == 'ios':
        h5_model_path = model_path.format("small_ios_model.h5")
        loop.run_until_complete(explora.start_new_session(repo_id, "IOS", h5_model_path))
    elif library == 'python':
        h5_model_path = model_path.format("my_model.h5")
        loop.run_until_complete(explora.start_new_session(repo_id, "PYTHON", h5_model_path))
    else:
        print("Library not supported!")