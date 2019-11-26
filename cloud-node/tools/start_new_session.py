from explora import Explora
import asyncio

explora = Explora()

repo_id = "99885f00eefcd4107572eb62a5cb429a"
library_type = "Javascript"

loop = asyncio.get_event_loop()

loop.run_until_complete(explora.start_new_session(repo_id, library_type))