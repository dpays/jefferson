# -*- coding: utf-8 -*-
import os
from copy import deepcopy
import ujson

from jefferson.upstream import _Upstreams
from jefferson.request.jsonrpc import JSONRPCRequest

from .conftest import TEST_UPSTREAM_CONFIG
from .conftest import AttrDict
from .conftest import make_request
from jefferson.request.jsonrpc import _empty
from jefferson.request.jsonrpc import from_http_request as jsonrpc_from_request


def test_request_id(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.id == jsonrpc_request.get('id')


def test_request_jsonrpc(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.jsonrpc == '2.0'


def test_request_method(full_urn_test_request_dict):
    jsonrpc_request, urn_parsed, urn, url, ttl, timeout = full_urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.method == jsonrpc_request['method']


def test_request_params(full_urn_test_request_dict):
    jsonrpc_request, urn_parsed, urn, url, ttl, timeout = full_urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.params == jsonrpc_request.get('params', _empty)


def test_request_urn(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.urn == urn


def test_request_upstream(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    os.environ['JEFFERSON_ACCOUNT_TRANSFER_DPAYD_URL'] = 'account_transfer_url'
    assert jefferson_request.upstream.url == url


def test_request_batch_index(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.batch_index == 0
    jefferson_request = jsonrpc_from_request(dummy_request, 1, jsonrpc_request)
    assert jefferson_request.batch_index == 1


def test_request_to_dict(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.to_dict() == jsonrpc_request


def test_request_to_json(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert ujson.loads(jefferson_request.json()) == jefferson_request.to_dict()


def test_upstream_id(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.upstream_id == 123

    jefferson_request = jsonrpc_from_request(dummy_request, 1, jsonrpc_request)
    assert jefferson_request.upstream_id == 124


def test_upstream_headers(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.upstream_headers == {
        'x-jefferson-request-id': '123',
        'x-amzn-trace-id': '123'}

    dummy_request.headers['x-amzn-trace-id'] = '1'
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    assert jefferson_request.upstream_headers == {
        'x-jefferson-request-id': '123',
        'x-amzn-trace-id': '1'
    }


def upstream_request(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)

    cpy = deepcopy(jefferson_request)
    cpy['id'] = 123456789012345
    assert jefferson_request.to_upstream_request(as_json=False) == cpy
    assert jefferson_request.to_upstream_request() == ujson.dumps(cpy,
                                                              ensure_ascii=False)

    cpy = deepcopy(jefferson_request)
    cpy['id'] = 123456789012346
    jefferson_request = jsonrpc_from_request(dummy_request, 1, cpy)
    assert jefferson_request.to_upstream_request(as_json=False) == cpy
    assert jefferson_request.to_upstream_request() == ujson.dumps(cpy,
                                                              ensure_ascii=False)


def test_log_extra():
    # TODO
    pass


def test_request_hash():
    # TODO
    pass
