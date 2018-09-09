# -*- coding: utf-8 -*-
from jefferson.urn import URN
import pytest
from jefferson.errors import InvalidNamespaceAPIError
from jefferson.upstream import _Upstreams
from .conftest import TEST_UPSTREAM_CONFIG
upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
namespaces = upstreams.namespaces
from jefferson.urn import from_request
from jefferson.urn import _parse_jrpc_method


def test_urns(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    result = str(from_request(jsonrpc_request))
    assert result == urn


@pytest.mark.parametrize("jsonrpc_request,expected", [
    # dpayd, bare_method
    ({'id': 1,
      'jsonrpc': '2.0',
      'method': 'get_account_count',
      'params': []},
     'dpayd.database_api.get_account_count.params=[]'
     ),
    # dpayd, method=call
    ({
        'id': 1,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_account_count', []]
    },
        'dpayd.database_api.get_account_count.params=[]'
    ),
    # dpayd, method=call, numeric api
    ({
        'id': 1,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': [0, 'get_account_count', []]
    },
        'dpayd.database_api.get_account_count.params=[]'
    ),
    # appbase, dotted method, condenser api
    ({
        'id': 1,
        'jsonrpc': '2.0',
        'method': 'condenser_api.appbase_method', 'params': []
    },
        'appbase.condenser_api.appbase_method.params=[]'
    ),
    # dpayd, condenser api, method=call
    ({
        'id': 1,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['condenser_api', 'appbase_method', []]
    },
        'appbase.condenser_api.appbase_method.params=[]'
    ),
    # namespace.api.method
    (
        {'id': 1,
         'jsonrpc': '2.0',
         'method': 'namespace.api.method',
         'params': []},
        'namespace.api.method.params=[]'
    ),
    # namespace.method
    (
        {'id': 1,
         'jsonrpc': '2.0',
         'method': 'namespace.method',
         'params': []},
        'namespace.method.params=[]'
    ),
])
def test_urn_params_empty_list(jsonrpc_request, expected):
    result = str(from_request(jsonrpc_request))
    assert result == expected


@pytest.mark.parametrize("jsonrpc_request,expected", [
    # appbase, dotted method, non-condenser api
    ({
        'id': 1, 'jsonrpc': '2.0',
        'method': 'non_condenser_api.appbase_method', 'params': {}
    },
        'appbase.non_condenser_api.appbase_method.params={}'
    ),

    # namespace.api.method
    (
        {'id': 1, 'jsonrpc': '2.0', 'method': 'namespace.api.method', 'params': {}},
        'namespace.api.method.params={}'
    ),
    # namespace.method
    (
        {'id': 1, 'jsonrpc': '2.0', 'method': 'namespace.method', 'params': {}},
        'namespace.method.params={}'
    ),
])
def test_urn_params_empty_dict(jsonrpc_request, expected):
    result = str(from_request(jsonrpc_request))
    assert result == expected


@pytest.mark.parametrize("jsonrpc_request,expected", [
    # dpayd, bare_method
    ({'id': 1, 'jsonrpc': '2.0', 'method': 'get_dynamic_global_properties'},
        'dpayd.database_api.get_dynamic_global_properties'
     ),
    # appbase, dotted method, non-condenser api
    ({'id': 1, 'jsonrpc': '2.0', 'method': 'non_condenser_api.appbase_method'},
        'appbase.non_condenser_api.appbase_method'
     ),

    # namespace.api.method
    ({'id': 1, 'jsonrpc': '2.0', 'method': 'namespace.api.method'},
        'namespace.api.method'
     ),
    # namespace.method
    (
        {'id': 1, 'jsonrpc': '2.0', 'method': 'namespace.method'},
        'namespace.method'
    ),
])
def test_urn_params_no_params(jsonrpc_request, expected):
    _parse_jrpc_method.cache_clear()
    result = str(from_request(jsonrpc_request))
    assert result == expected


def test_invalid_numeric_dpayd_api():
    jsonrpc_request = {
        'id': 11,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': [2, "login", ["", ""]]
    }
    with pytest.raises(InvalidNamespaceAPIError):
        result = str(from_request(jsonrpc_request))


def test_urn_pairs(dpayd_method_pairs):
    old, new = dpayd_method_pairs
    old_urn = str(from_request(old))
    new_urn = str(from_request(new))
    assert old_urn == new_urn
    assert old_urn.startswith('dpayd.database_api')
