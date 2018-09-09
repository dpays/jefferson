# -*- coding: utf-8 -*-
import pytest

from jefferson.cache.ttl import TTL
from jefferson.cache.utils import irreversible_ttl
from jefferson.request.jsonrpc import JSONRPCRequest
from jefferson.request.jsonrpc import from_http_request as jsonrpc_from_request
from .conftest import make_request
dummy_request = make_request()


ttl_rpc_req = jsonrpc_from_request(dummy_request, 0, {"id": "1", "jsonrpc": "2.0",
                                                      "method": "get_block", "params": [1000]})
rpc_resp = {
    "id": 1,
    "result": {
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
    }}

non_ttl_rpc_req = jsonrpc_from_request(dummy_request, 0, {"id": "1", "jsonrpc": "2.0",
                                                          "method": "dpds.method", "params": [1000]})


@pytest.mark.parametrize('rpc_req, rpc_resp, last_block_num, expected', [
    # don't cache when last_block_num < response block_num
    (ttl_rpc_req, rpc_resp, 1, TTL.DEFAULT_TTL),
    (ttl_rpc_req, rpc_resp, 999, TTL.DEFAULT_TTL),

    # cache when last_block_num >= response block_num
    (ttl_rpc_req, rpc_resp, 1000, TTL.NO_EXPIRE),
    (ttl_rpc_req, rpc_resp, 1001, TTL.NO_EXPIRE),

    # don't cache when bad/missing response block_num
    (ttl_rpc_req, {}, 2000, TTL.NO_CACHE),
    (ttl_rpc_req, {}, None, TTL.NO_CACHE),

])
def test_ttls(rpc_req, rpc_resp, last_block_num, expected):
    ttl = irreversible_ttl(rpc_resp, last_block_num)
    if isinstance(expected, TTL):
        expected = expected.value
    assert ttl == expected


@pytest.mark.parametrize('ttl,eq', [
    (TTL.NO_CACHE, -1),
    (TTL.DEFAULT_TTL, 3),
    (TTL.NO_EXPIRE, None),
    (TTL.NO_EXPIRE_IF_IRREVERSIBLE, -2),
]
)
def test_ttl_eq(ttl, eq):
    assert ttl == ttl
    assert ttl == eq


@pytest.mark.parametrize('ttl', [
    (TTL.NO_CACHE),
    (TTL.DEFAULT_TTL),
    (TTL.NO_EXPIRE_IF_IRREVERSIBLE)
]
)
def test_ttl_gt(ttl):
    assert ttl > -3


@pytest.mark.parametrize('ttl', [
    (TTL.NO_CACHE),
    (TTL.DEFAULT_TTL),
    (TTL.NO_EXPIRE_IF_IRREVERSIBLE)
]
)
def test_ttl_ge(ttl):
    assert ttl >= -2


@pytest.mark.parametrize('ttl', [
    (TTL.NO_CACHE),
    (TTL.DEFAULT_TTL),
    (TTL.NO_EXPIRE_IF_IRREVERSIBLE)
]
)
def test_ttl_lt(ttl):
    assert ttl < 4


@pytest.mark.parametrize('ttl', [
    (TTL.NO_CACHE),
    (TTL.DEFAULT_TTL),
    (TTL.NO_EXPIRE_IF_IRREVERSIBLE)
]
)
def test_ttl_le(ttl):
    assert ttl <= 3
