# -*- coding: utf-8 -*-
import os

from .conftest import TEST_UPSTREAM_CONFIG

from jefferson.upstream import Upstream
from jefferson.upstream import _Upstreams
from jefferson.urn import URN
from jefferson.urn import from_request


def test_upstream_url(urn_test_request_dict):
    os.environ['JEFFERSON_ACCOUNT_TRANSFER_DPAYD_URL'] = 'account_transfer_url'
    upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    test_urn = from_request(jsonrpc_request)
    upstream = Upstream.from_urn(test_urn, upstreams=upstreams)
    del os.environ['JEFFERSON_ACCOUNT_TRANSFER_DPAYD_URL']
    assert upstream.url == url


def test_upstream_ttl(urn_test_request_dict):
    upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    test_urn = from_request(jsonrpc_request)
    upstream = Upstream.from_urn(test_urn, upstreams=upstreams)
    assert upstream.ttl == ttl


def test_upstream_timeout(urn_test_request_dict):
    upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    test_urn = from_request(jsonrpc_request)
    upstream = Upstream.from_urn(test_urn, upstreams=upstreams)
    assert upstream.timeout == timeout
