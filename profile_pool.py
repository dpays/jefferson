# -*- coding: utf-8 -*-
import asyncio
import cProfile
import uvloop

from jussi.ws.pool2 import Pool
# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

pr = cProfile.Profile()


async def run(pool, count):
    pr.enable()
    for i in range(count):
        conn = await pool.acquire()
        await pool.release(conn)
    pr.disable()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(Pool(
        1,  # minsize of pool
        2,  # maxsize of pool
        0,  # max queries per conn (0 means unlimited)
        loop,  # event_loop
        'ws://127.0.0.1',  # connection url
        # all kwargs are passed to websocket connection
    ))
    loop.run_until_complete(run(pool, 10000))
    pr.print_stats(sort='time')
