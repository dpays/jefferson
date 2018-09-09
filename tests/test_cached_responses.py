# -*- coding: utf-8 -*-


import pytest

from jefferson.cache.utils import jsonrpc_cache_key
from jefferson.request.jsonrpc import JSONRPCRequest
from .conftest import make_request
from jefferson.request.jsonrpc import from_http_request as jsonrpc_from_request


jrpc_req_1 = jsonrpc_from_request(make_request(), 0, {"id": "1", "jsonrpc": "2.0",
                                                      "method": "get_block", "params": [1000]})
jrpc_resp_1 = {
    "id":1,
    "result":{
        "previous":"000003e70301334402ae97d8cef292a21247777f",
        "timestamp":"2018-09-04T17:33:18",
        "witness":"dpay",
        "transaction_merkle_root":"0000000000000000000000000000000000000000",
        "extensions":[],
        "witness_signature":"205e1849df241ceb359d0f738f758be42ca55f3e345cd017ab3fff68c00f264c24373876fbafeacf2905914cea8d329df9f1cdd18d3b662d96579ebb10e75b77c5",
        "transactions":[],
        "block_id":"000003e8cc14da92f6beb0f9949a672cda19dd7b",
        "signing_key":"DWB88FC9nDFczSTfVxrzHvVe8ZuvajLHKikfJYWiKkNvrUebBovzF",
        "transaction_ids":[]
    }
}


batch1_jrpc = [jsonrpc_from_request(make_request(), _id, {"id": _id, "jsonrpc": "2.0",
                                                          "method": "get_block", "params": [1000]}) for _id in range(10)]
batch2_jrpc = [jsonrpc_from_request(make_request(), _id, {"id": _id, "jsonrpc": "2.0", "method": "get_block",
                                                          "params": [1000]}) for _id in range(20, 30)]

cached_resp1 = [None for i in batch1_jrpc]
cached_resp2 = [
    None,
    {"id": 99, "jsonrpc": "2.0", "method": "get_block", "params": [1000]},
    None,
    {"id": 98, "jsonrpc": "2.0", "method": "get_block", "params": [1000]}]
expected2 = [None,
             {"id": 1, "jsonrpc": "2.0",
                 "method": "get_block", "params": [1000]},
             None,
             {"id": 3, "jsonrpc": "2.0",
                 "method": "get_block", "params": [1000]},
             ]


@pytest.mark.parametrize('jrpc_batch_req,responses, expected', [
    (batch1_jrpc, cached_resp1, cached_resp1),
    (batch1_jrpc, batch2_jrpc, batch2_jrpc),
    (batch1_jrpc[:4], cached_resp2, expected2)
])
def merge_cached_responses(jrpc_batch_req, responses, expected):
    assert merge_cached_responses(jrpc_batch_req, responses) == expected


@pytest.mark.parametrize('cached,jrpc_batch_req,expected', [
    (batch1_jrpc, batch2_jrpc, batch2_jrpc)
])
def cache_get_batch(loop, caches, cached, jrpc_batch_req, expected):
    for cache in caches:
        loop.run_until_complete(cache.clear())

    for item in cached:
        if 'id' in cached:
            del cached['id']
        key = jsonrpc_cache_key(item)
        for cache in caches:
            loop.run_until_complete(
                cache.set(key, item, ttl=None))

    results = loop.run_until_complete(cache_get_batch(caches, jrpc_batch_req))
    assert results == expected
