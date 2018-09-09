# -*- coding: utf-8 -*-
import pytest


from jefferson.cache.utils import block_num_from_jsonrpc_response

# FIXME add all formats of get_block and get_block_header responses
ttl_rpc_req = {"id": "1", "jsonrpc": "2.0",
               "method": "get_block", "params": [1000]}
rpc_resp = {
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

non_ttl_rpc_req = {"id": "1", "jsonrpc": "2.0",
                   "method": "dpds.get_block", "params": [1000]}


@pytest.mark.parametrize('response,expected', [
    (rpc_resp, 1000)
])
def test_block_num_from_jsonrpc_response(response, expected):
    num = block_num_from_jsonrpc_response(response)
    assert num == expected
