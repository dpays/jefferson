# -*- coding: utf-8 -*-
from jefferson.cache.utils import jsonrpc_cache_key


def test_cache_key(urn_test_requests):
    jsonrpc_request, urn, url, ttl, timeout, jefferson_request = urn_test_requests
    result = jsonrpc_cache_key(jefferson_request)
    assert result == urn
