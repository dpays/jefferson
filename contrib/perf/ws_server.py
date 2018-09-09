# -*- coding: utf-8 -*-
from sanic import Sanic
from sanic.response import json
import ujson
app = Sanic()

resp = {
    "id": 1,
    "jsonrpc": "2.0",
    "result": {
        "block_id": "000000011b5056ef5b610531031204f173aef7a8",
        "extensions": [],
        "previous": "0000000000000000000000000000000000000000",
        "signing_key": "DWB88FC9nDFczSTfVxrzHvVe8ZuvajLHKikfJYWiKkNvrUebBovzF",
        "timestamp": "2018-09-04T16:36:27",
        "transaction_ids": [],
        "transaction_merkle_root": "0000000000000000000000000000000000000000",
        "transactions": [],
        "witness": "dpay",
        "witness_signature": "201522e89ede4eea643486772bb7cf5fd59224f0de226840124651dcb7a22251d772e1a8a953d7218eddf83618351f33ec401007713070b435253d44a3ad937db2"
    }
}
resp_json = ujson.dumps(resp).encode('utf8')


@app.route("/hello")
async def test(request):
    return json({"hello": "world"})


@app.websocket('/')
async def feed(request, ws):
    while True:
        await ws.send(resp_json)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
