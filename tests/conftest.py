# -*- coding: utf-8 -*-
import ujson
import asynctest
import copy
import itertools as it
import jsonschema
import os
import pytest
import requests
import requests.exceptions
import sanic
import sanic.response
from funcy.funcs import rpartial

from typing import Union
from typing import Sequence
from typing import List

import tests.data.jsonrpc.invalid

import jefferson.errors
import jefferson.handlers
import jefferson.listeners
import jefferson.logging_config
import jefferson.middlewares
import jefferson.serve
from jefferson.cache.backends.max_ttl import SimplerMaxTTLMemoryCache
from jefferson.cache.backends.redis import Cache
from jefferson.cache.backends.redis import MockClient
from jefferson.urn import URN
from jefferson.empty import _empty
from jefferson.upstream import _Upstreams
from jefferson.request.jsonrpc import from_http_request as jsonrpc_from_request
from jefferson.request.http import HTTPRequest


TEST_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_DATA_DIR = os.path.join(TEST_DIR, 'data')
SCHEMA_DIR = os.path.join(TEST_DATA_DIR, 'schema')
REQS_AND_RESPS_DIR = os.path.join(TEST_DATA_DIR, 'jsonrpc')
CONFIGS_DIR = os.path.join(TEST_DATA_DIR, 'configs')


def chunks(l: Sequence, n: int) -> List[List]:
    """Yield successive n-sized chunks from l."""
    chunk = []
    for item in l:
        while len(chunk) < n:
            chunk.append(item)
        yield chunk
        chunk = []
    if len(chunk) > 0:
        yield chunk

# ------------------------
# pytest config functions
# ------------------------


def pytest_addoption(parser):
    parser.addoption("--rundocker", action="store_true",
                     default=False, help="run docker tests")

    parser.addoption("--jeffersonurl", action="store",
                     help="url to use for integration level jefferson tests")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if 'route' in item.nodeid:
            item.add_marker(pytest.mark.test_app)
    if not config.getoption("--rundocker") and not config.getoption("--jeffersonurl"):
        skip_live = pytest.mark.skip(reason="need --rundocker or --jeffersonurl option to run")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)


@pytest.fixture(scope='function')
def jefferson_url(request):
    if request.config.getoption("--rundocker"):
        # request.config.getoption("--jeffersonurl")
        return request.getfixturevalue('jefferson_docker_service')
    else:
        return request.config.getoption("--jeffersonurl")


# ------------------------
# schema loading fixtures
# ------------------------

@pytest.fixture
def jrpc_request_schema():
    with open(os.path.join(SCHEMA_DIR, 'request-schema.json')) as f:
        return ujson.load(f)


@pytest.fixture
def jrpc_response_schema():
    with open(os.path.join(SCHEMA_DIR, 'response-schema.json')) as f:
        return ujson.load(f)


@pytest.fixture
def dpayd_response_schema():
    with open(os.path.join(SCHEMA_DIR, 'dpayd-response-schema.json')) as f:
        return ujson.load(f)


with open(os.path.join(CONFIGS_DIR, 'TEST_UPSTREAM_CONFIG.json')) as f:
    TEST_UPSTREAM_CONFIG = ujson.load(f)


# ------------------------
# request/response loading fixtures
# ------------------------

def dpayd_requests_and_responses():
    with open(os.path.join(REQS_AND_RESPS_DIR, 'dpayd.json')) as f:
        return ujson.load(f)


def batched_dpayd_requests_and_responses(chunk_size=15):
    requests = chunks(
        [req for req, resp in dpayd_requests_and_responses()], chunk_size)
    responses = chunks(
        [resp for req, resp in dpayd_requests_and_responses()], chunk_size)
    return list(zip(requests, responses))


def appbase_requests_and_responses():
    with open(os.path.join(REQS_AND_RESPS_DIR, 'appbase.json')) as f:
        return ujson.load(f)


def batched_appbase_requests_and_responses(chunk_size=15):
    requests = chunks(
        [req for req, resp in appbase_requests_and_responses()], chunk_size)
    responses = chunks(
        [resp for req, resp in appbase_requests_and_responses()], chunk_size)
    return list(zip(requests, responses))


def combined_requests_and_responses():
    return dpayd_requests_and_responses() + appbase_requests_and_responses()


def batch_combined_requests(chunk_size=15):
    return list(
        chunks(
            [req for req, resp in combined_requests_and_responses()],
            chunk_size)
    )


@pytest.fixture
def translatable_dpayd_requests_and_responses():
    import jefferson.urn
    untranslateable = frozenset(['get_liquidity_queue', 'get_miner_queue',
                                 'get_discussions_by_payout'])
    return [(req, resp) for req, resp in dpayd_requests_and_responses()
            if jefferson.urn.from_request(req).method not in untranslateable]


def batch_translatable_requests_and_responses(chunk_size=15):
    requests = chunks(
        [req for req, resp in translatable_dpayd_requests_and_responses()], chunk_size)
    responses = chunks(
        [resp for req, resp in translatable_dpayd_requests_and_responses()], chunk_size)
    return list(zip(requests, responses))


@pytest.fixture
def appbase_requests(appbase_requests_and_responses):
    return [p[0] for p in appbase_requests_and_responses]


DPAYD_JSON_RPC_CALLS = [
    {
        'id': 0,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_account_count',
                   []]
    },
    {
        'id': 1,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_account_history',
                   ['dpay', 20, 10]]
    },
    {
        'id': 2,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_account_votes',
                   ['dpay', 'test']]
    },
    {
        'id': 3,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_accounts',
                   [['dpay']]]
    },
    {
        'id': 4,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_active_votes',
                   ['smooth', 'test']]
    },
    {
        'id': 5,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_active_witnesses',
                   []]
    },
    {
        'id': 6,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_block_header',
                   [1000]]
    },
    {
        'id': 7,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_chain_properties',
                   []]
    },
    {
        'id': 8,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_config', []]
    },
    {
        'id': 9,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_content',
                   ['dpay', 'test']]
    },
    {
        'id': 10,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_content_replies',
                   ['dpay', 'test']]
    },
    {
        'id': 11,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_conversion_requests', ['dpay']]
    },
    {
        'id': 12,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_current_median_history_price', []]
    },
    {
        'id': 13,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_active',
                   [{'limit': '1', 'tag': 'dpay'}]]
    },
    {
        'id': 14,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_author_before_date',
                   ['smooth', 'test',
                    '2016-07-23T22:00:06', '1']]
    },
    {
        'id': 15,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_cashout',
                   [{'limit': '1', 'tag': 'dpay'}]]
    },
    {
        'id': 16,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_children',
                   [{'limit': '1', 'tag': 'dpay'}]]
    },
    {
        'id': 17,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_created',
                   [{'limit': '1', 'tag': 'dpay'}]]
    },
    {
        'id': 18,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_feed',
                   [{'limit': '1', 'tag': 'dpay'}]]
    },
    {
        'id': 19,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_hot',
                   [{'limit': '1', 'tag': 'dpay'}]]
    },
    {
        'id': 20,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_payout',
                   [{'limit': '1', 'tag': 'dpay'}]]
    },
    {
        'id': 21,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_trending',
                   [{'limit': '1', 'tag': 'dpay'}]]
    },
    {
        'id': 22,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_discussions_by_votes',
                   [{'limit': '1', 'tag': 'dpay'}]]
    },
    {
        'id': 23,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_dynamic_global_properties', []]
    },
    {
        'id': 24,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_feed_history', []]
    },
    {
        'id': 25,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_hardfork_version',
                   []]
    },
    {
        'id': 26,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_liquidity_queue',
                   ['dpay', 10]]
    },
    {
        'id': 27,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_miner_queue', []]
    },
    {
        'id': 28,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_next_scheduled_hardfork',
                   ['dpay', 10]]
    },
    {
        'id': 29,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_open_orders',
                   ['dpay']]
    },
    {
        'id': 30,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_order_book', [10]]
    },
    {
        'id': 31,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_owner_history',
                   ['dpay']]
    },
    {
        'id': 32,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_recovery_request',
                   ['dpay']]
    },
    {
        'id': 33,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_replies_by_last_update',
                   ['smooth', 'test', 10]]
    },
    {
        'id': 34,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_state',
                   ['/@dpay']]
    },
    {
        'id': 35,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_trending_tags',
                   ['dpay', 10]]
    },
    {
        'id': 36,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'get_witness_by_account',
                   ['smooth.witness']]
    },
    {
        'id': 37,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_witness_count',
                   []]
    },
    {
        'id': 38,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_witness_schedule',
                   []]
    },
    {
        'id': 39,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'lookup_account_names',
                   [['dpay']]]
    },
    {
        'id': 40,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'lookup_accounts',
                   ['dpay', 10]]
    },
    {
        'id': 41,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api',
                   'lookup_witness_accounts',
                   ['dpay', 10]]
    },
    {
        'id': 42, 'jsonrpc': '2.0',
        'method': 'get_account_count', 'params': []
    },
    {
        'id': 43,
        'jsonrpc': '2.0',
        'method': 'get_account_history',
        'params': ['dpay', 20, 10]
    },
    {
        'id': 44,
        'jsonrpc': '2.0',
        'method': 'get_account_votes',
        'params': ['dpay', 'test']
    },
    {
        'id': 45,
        'jsonrpc': '2.0',
        'method': 'get_accounts',
        'params': [['dpay']]
    },
    {
        'id': 46,
        'jsonrpc': '2.0',
        'method': 'get_active_votes',
        'params': ['smooth', 'test']
    },
    {
        'id': 47, 'jsonrpc': '2.0',
        'method': 'get_active_witnesses', 'params': []
    },
    {
        'id': 48, 'jsonrpc': '2.0',
        'method': 'get_block_header', 'params': [1000]
    },
    {
        'id': 49, 'jsonrpc': '2.0',
        'method': 'get_chain_properties', 'params': []
    },
    {
        'id': 50, 'jsonrpc': '2.0',
        'method': 'get_config', 'params': []
    },
    {
        'id': 51,
        'jsonrpc': '2.0',
        'method': 'get_content',
        'params': ['dpay', 'test']
    },
    {
        'id': 52,
        'jsonrpc': '2.0',
        'method': 'get_content_replies',
        'params': ['dpay', 'test']
    },
    {
        'id': 53,
        'jsonrpc': '2.0',
        'method': 'get_conversion_requests',
        'params': ['dpay']
    },
    {
        'id': 54,
        'jsonrpc': '2.0',
        'method': 'get_current_median_history_price',
        'params': []
    },
    {
        'id': 55,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_active',
        'params': [{'limit': '1', 'tag': 'dpay'}]
    },
    {
        'id': 56,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_author_before_date',
        'params': ['smooth', 'test',
                   '2016-07-23T22:00:06', '1']
    },
    {
        'id': 57,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_cashout',
        'params': [{'limit': '1', 'tag': 'dpay'}]
    },
    {
        'id': 58,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_children',
        'params': [{'limit': '1', 'tag': 'dpay'}]
    },
    {
        'id': 59,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_created',
        'params': [{'limit': '1', 'tag': 'dpay'}]
    },
    {
        'id': 60,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_feed',
        'params': [{'limit': '1', 'tag': 'dpay'}]
    },
    {
        'id': 61,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_hot',
        'params': [{'limit': '1', 'tag': 'dpay'}]
    },
    {
        'id': 62,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_payout',
        'params': [{'limit': '1', 'tag': 'dpay'}]
    },
    {
        'id': 63,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_trending',
        'params': [{'limit': '1', 'tag': 'dpay'}]
    },
    {
        'id': 64,
        'jsonrpc': '2.0',
        'method': 'get_discussions_by_votes',
        'params': [{'limit': '1', 'tag': 'dpay'}]
    },
    {
        'id': 65,
        'jsonrpc': '2.0',
        'method': 'get_dynamic_global_properties',
        'params': []
    },
    {
        'id': 66, 'jsonrpc': '2.0',
        'method': 'get_feed_history', 'params': []
    },
    {
        'id': 67, 'jsonrpc': '2.0',
        'method': 'get_hardfork_version', 'params': []
    },
    {
        'id': 68,
        'jsonrpc': '2.0',
        'method': 'get_liquidity_queue',
        'params': ['dpay', 10]
    },
    {
        'id': 69, 'jsonrpc': '2.0',
        'method': 'get_miner_queue', 'params': []
    },
    {
        'id': 70,
        'jsonrpc': '2.0',
        'method': 'get_next_scheduled_hardfork',
        'params': ['dpay', 10]
    },
    {
        'id': 71,
        'jsonrpc': '2.0',
        'method': 'get_open_orders',
        'params': ['dpay']
    },
    {
        'id': 72, 'jsonrpc': '2.0',
        'method': 'get_order_book', 'params': [10]
    },
    {
        'id': 73,
        'jsonrpc': '2.0',
        'method': 'get_owner_history',
        'params': ['dpay']
    },
    {
        'id': 74,
        'jsonrpc': '2.0',
        'method': 'get_recovery_request',
        'params': ['dpay']
    },
    {
        'id': 75,
        'jsonrpc': '2.0',
        'method': 'get_replies_by_last_update',
        'params': ['smooth', 'test', 10]
    },
    {
        'id': 76, 'jsonrpc': '2.0',
        'method': 'get_state', 'params': ['/@layz3r']
    },
    {
        'id': 77,
        'jsonrpc': '2.0',
        'method': 'get_trending_tags',
        'params': ['dpay', 10]
    },
    {
        'id': 78,
        'jsonrpc': '2.0',
        'method': 'get_witness_by_account',
        'params': ['smooth.witness']
    },
    {
        'id': 79, 'jsonrpc': '2.0',
        'method': 'get_witness_count', 'params': []
    },
    {
        'id': 80, 'jsonrpc': '2.0',
        'method': 'get_witness_schedule', 'params': []
    },
    {
        'id': 81,
        'jsonrpc': '2.0',
        'method': 'lookup_account_names',
        'params': [['dpay']]
    },
    {
        'id': 82,
        'jsonrpc': '2.0',
        'method': 'lookup_accounts',
        'params': ['dpay', 10]
    },
    {
        'id': 83,
        'jsonrpc': '2.0',
        'method': 'lookup_witness_accounts',
        'params': ['dpay', 10]
    }

]

DPAYD_JSONRPC_CALL_PAIRS = []
for c in DPAYD_JSON_RPC_CALLS:
    if c['method'] == 'call':
        method = c['params'][1]
        new_method = [
            m for m in DPAYD_JSON_RPC_CALLS if m['method'] == method]
        DPAYD_JSONRPC_CALL_PAIRS.append((c, new_method[0]))

LONG_REQUESTS = [
    {
        'id': 1,
        'jsonrpc': '2.0',
        'method': 'get_accounts',
        'params': [["dpay", "jared", "stan", "michaelx", "nomoreheroes", "onceuponatime", "lana", "mbex", "cointroller", "freedomfirst", "bigg", "morrison", "chiraag", "nickeles", "stormkrow", "kusknee", "tablecafe", "bossdan", "cryptokong", "lune", "quin", "whi", "dsite", "dpayid", "maga"]]
    }
]

# pylint:  disable=unused-variable,unused-argument,attribute-defined-outside-init

URN_TEST_REQUEST_DICTS = [
    # --------APPBASE METHOD=CALL, CONDENSER----------------------
    # appbase, method=call, condenser api, params empty list
    ({
        'id': 1001,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['condenser_api', 'get_dynamic_global_properties', []]
    }, {
        'namespace': 'appbase',
        'api': 'condenser_api',
        'method': 'get_dynamic_global_properties',
        'params': []
    },
        'appbase.condenser_api.get_dynamic_global_properties.params=[]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, method=call, condenser api, params list of empty list
    ({
        'id': 1002,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['condenser_api', 'get_accounts', [[]]]
    },
        {
        'namespace': 'appbase',
        'api': 'condenser_api',
        'method': 'get_accounts',
        'params': [[]]
    },
        'appbase.condenser_api.get_accounts.params=[[]]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),

    # appbase, method=call, condenser api, params list
    ({
        'id': 1003,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['condenser_api', 'get_accounts', [['dpay']]]
    },
        {
        'namespace': 'appbase',
        'api': 'condenser_api',
        'method': 'get_accounts',
        'params': [['dpay']]
    },
        'appbase.condenser_api.get_accounts.params=[["dpay"]]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, method=call, condenser api, params list
    ({
        "id": "1004",
        "jsonrpc": "2.0",
        "method": "call",
        "params": ["condenser_api", "get_block", [1000]]
    },
        {
        'namespace': 'appbase',
        'api': 'condenser_api',
        'method': 'get_block',
        'params': [1000]
    },
        'appbase.condenser_api.get_block.params=[1000]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # ----------APPBASE METHOD=CALL, NON-CONDENSER-------------------
    # appbase, method=call, non-condenser api,  no params
    ({
        'id': 2005,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['appbase_api', 'appbase_method']
    },
        {
        'namespace': 'appbase',
        'api': 'appbase_api',
        'method': 'appbase_method',
        'params': _empty
    },
        'appbase.appbase_api.appbase_method',
        'wss://greatchain.dpays.io',
        3,
        3
    ),

    # appbase, method=call, non-condenser api, empty params dict
    ({
        'id': 2007,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['appbase_api', 'appbase_method', {}]
    },
        {
        'namespace': 'appbase',
        'api': 'appbase_api',
        'method': 'appbase_method',
        'params': {}
    },
        'appbase.appbase_api.appbase_method.params={}',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, method=call, non-condenser api, no params
    ({
        'id': 2008,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['appbase_api', 'appbase_method']
    },
        {
        'namespace': 'appbase',
        'api': 'appbase_api',
        'method': 'appbase_method',
        'params': _empty
    },
        'appbase.appbase_api.appbase_method',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, method=call, non-condenser api, params dict
    ({
        'id': 2009,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['block_api', 'get_block', {'block_num': 23}]
    },
        {
        'namespace': 'appbase',
        'api': 'block_api',
        'method': 'get_block',
        'params': {'block_num': 23}
    },
        'appbase.block_api.get_block.params={"block_num":23}',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, method=call, jsonrpc api, no params
    ({
        'id': 2010,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['jsonrpc', 'get_methods']
    },
        {
        'namespace': 'appbase',
        'api': 'jsonrpc',
        'method': 'get_methods',
        'params': _empty

    },
        'appbase.jsonrpc.get_methods',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, method=call, jsonrpc api, empty params dict
    ({
        'id': 2011,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['jsonrpc', 'get_methods', {}]
    },
        {
        'namespace': 'appbase',
        'api': 'jsonrpc',
        'method': 'get_methods',
        'params': {}

    },
        'appbase.jsonrpc.get_methods.params={}',
        'wss://greatchain.dpays.io',
        3,
        3
    ),

    #----------APPBASE DOTTED CONDENSER---------------------
    # appbase, dotted.method, condenser api, params list
    ({
        "id": "3010",
        "jsonrpc": "2.0",
        "method": "condenser_api.get_block",
        "params": [1000]
    },
        {
        'namespace': 'appbase',
        'api': 'condenser_api',
        'method': 'get_block',
        'params': [1000]
    },
        'appbase.condenser_api.get_block.params=[1000]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, dotted method, condenser api, params list
    ({
        'id': 3011,
        'jsonrpc': '2.0',
        'method': 'condenser_api.get_accounts',
        'params': [['dpay']]
    },
        {
        'namespace': 'appbase',
        'api': 'condenser_api',
        'method': 'get_accounts',
        'params': [['dpay']]
    },
        'appbase.condenser_api.get_accounts.params=[["dpay"]]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),

    # appbase, dotted method, condenser api, params list of empty list
    ({
        'id': 3012,
        'jsonrpc': '2.0',
        'method': 'condenser_api.get_accounts',
        'params': [[]]
    },
        {
        'namespace': 'appbase',
        'api': 'condenser_api',
        'method': 'get_accounts',
        'params': [[]]
    },
        'appbase.condenser_api.get_accounts.params=[[]]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),

    ({
        'id': 3014,
        'jsonrpc': '2.0',
        'method': 'condenser_api.get_dynamic_global_properties',
        'params': []
    },
        {
        'namespace': 'appbase',
        'api': 'condenser_api',
        'method': 'get_dynamic_global_properties',
        'params': []
    },
        'appbase.condenser_api.get_dynamic_global_properties.params=[]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),

    # ----------APPBASE DOTTED NON-CONDENSER---------------------
    # appbase, dotted method, non-condenser api, no params
    ({
        'id': 4015,
        'jsonrpc': '2.0',
        'method': 'appbase_api.appbase_method'
    },
        {
        'namespace': 'appbase',
        'api': 'appbase_api',
        'method': 'appbase_method',
        'params': _empty
    },
        'appbase.appbase_api.appbase_method',
        'wss://greatchain.dpays.io',
        3,
        3
    ),

    # appbase, dotted method, non-condenser api, empty params list
    ({
        'id': 4016,
        'jsonrpc': '2.0',
        'method': 'appbase_api.appbase_method',
        'params': []
    },
        {
        'namespace': 'appbase',
        'api': 'appbase_api',
        'method': 'appbase_method',
        'params': []
    },
        'appbase.appbase_api.appbase_method.params=[]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, dotted method, non-condenser api, empty params dict
    ({
        'id': 4017,
        'jsonrpc': '2.0',
        'method': 'appbase_api.appbase_method',
        'params': {}
    },
        {
        'namespace': 'appbase',
        'api': 'appbase_api',
        'method': 'appbase_method',
        'params': {}
    },
        'appbase.appbase_api.appbase_method.params={}',
        'wss://greatchain.dpays.io',
        3,
        3
    ),

    # appbase, dotted method, non-condenser api, params dict
    ({
        'id': 4018,
        'jsonrpc': '2.0',
        'method': 'appbase_api.appbase_method',
        'params': {'accounts': ['dpay']}
    },
        {
        'namespace': 'appbase',
        'api': 'appbase_api',
        'method': 'appbase_method',
        'params': {'accounts': ['dpay']}
    },
        'appbase.appbase_api.appbase_method.params={"accounts":["dpay"]}',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, dotted method, non-condenser api, params list
    ({
        'id': 4019,
        'jsonrpc': '2.0',
        'method': 'appbase_api.appbase_method',
        'params': [1]
    },
        {
        'namespace': 'appbase',
        'api': 'appbase_api',
        'method': 'appbase_method',
        'params': [1]
    },
        'appbase.appbase_api.appbase_method.params=[1]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, dotted method, jsonrpc api, no params
    ({
        'id': 4019,
        'jsonrpc': '2.0',
        'method': 'jsonrpc.get_methods'
    },
        {
        'namespace': 'appbase',
        'api': 'jsonrpc',
        'method': 'get_methods',
        'params': _empty

    },
        'appbase.jsonrpc.get_methods',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # appbase, dotted method, jsonrpc api, empty params dict
    ({
        'id': 4020,
        'jsonrpc': '2.0',
        'method': 'jsonrpc.get_methods',
        'params': {}
    },
        {
        'namespace': 'appbase',
        'api': 'jsonrpc',
        'method': 'get_methods',
        'params': {}

    },
        'appbase.jsonrpc.get_methods.params={}',
        'wss://greatchain.dpays.io',
        3,
        3
    ),

    # -------- DPAYD BARE METHOD ----------------
    # dpayd, bare method, no params
    ({
        'id': 5020,
        'jsonrpc': '2.0',
        'method': 'get_dynamic_global_properties'
    },
        {
        'namespace': 'dpayd',
        'api': 'database_api',
        'method': 'get_dynamic_global_properties',
        'params': _empty
    },
        'dpayd.database_api.get_dynamic_global_properties',
        'wss://greatchain.dpays.io',
        1,
        3
    ),
    # dpayd, bare method, empty params list
    ({
        'id': 5021,
        'jsonrpc': '2.0',
        'method': 'get_dynamic_global_properties',
        'params': []
    },
        {
        'namespace': 'dpayd',
        'api': 'database_api',
        'method': 'get_dynamic_global_properties',
        'params': []
    },
        'dpayd.database_api.get_dynamic_global_properties.params=[]',
        'wss://greatchain.dpays.io',
        1,
        3
    ),
    # dpayd, bare method, params list
    ({
        'id': 5022,
        'jsonrpc': '2.0',
        'method': 'get_block',
        'params': [1]
    },
        {
        'namespace': 'dpayd',
        'api': 'database_api',
        'method': 'get_block',
        'params': [1]
    },
        'dpayd.database_api.get_block.params=[1]',
        'wss://greatchain.dpays.io',
        -2,
        3
    ),

    # dpayd, bare_method, account transfer url
    ({
        "id": 5023,
        "jsonrpc": "2.0",
        "method": "get_state",
        "params": ["/@dpay/transfers"]
    },
        {
        'namespace': 'dpayd',
        'api': 'database_api',
        'method': 'get_state',
        'params': ["/@dpay/transfers"]
    },
        'dpayd.database_api.get_state.params=["\/@dpay\/transfers"]',
        'account_transfer_url',
        1,
        3
    ),


    # -------- DPAYD METHOD=CALL ----------------


    # dpayd, method=call, empty params list
    ({
        'id': 5024,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': ['database_api', 'get_account_count', []]
    },
        {
        'namespace': 'dpayd',
        'api': 'database_api',
        'method': 'get_account_count',
        'params': []
    },
        'dpayd.database_api.get_account_count.params=[]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # dpayd numeric apis
    ({
        'id': 5025,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': [1, "login", ["", ""]]
    },
        {
        'namespace': 'dpayd',
        'api': 'login_api',
        'method': 'login',
        'params': ["", ""]
    },
        'dpayd.login_api.login.params=["",""]',
        'wss://greatchain.dpays.io',
        -1,
        3
    ),
    ({
        'id': 5026,
        'jsonrpc': '2.0',
        'method': 'call',
        'params': [0, "find_accounts", []]
    },
        {
        'namespace': 'dpayd',
        'api': 'database_api',
        'method': 'find_accounts',
        'params': []
    },
        'dpayd.database_api.find_accounts.params=[]',
        'wss://greatchain.dpays.io',
        3,
        3
    ),
    # dpayd, method=call, account transfer url
    ({
        "id": 5027,
        "jsonrpc": "2.0",
        "method": "call",
        "params": ["database_api", "get_state", [r"/@dpay/transfers"]]
    },
        {
        'namespace': 'dpayd',
        'api': 'database_api',
        'method': 'get_state',
        'params': ["/@dpay/transfers"]
    },
        'dpayd.database_api.get_state.params=["\/@dpay\/transfers"]',
        'account_transfer_url',
        1,
        3
    ),


    # -------NAMESPACE.METHOD-------------

    # namespace.method, params triple
    ({
        'id': 6026,
        'jsonrpc': '2.0',
        'method': 'namespace.method',
        'params': ['database_api', 'get_account_count', []]
    },
        {
        'namespace': 'namespace',
        'api': _empty,
        'method': 'method',
        'params': ['database_api', 'get_account_count', []]
    },
        'namespace.method.params=["database_api","get_account_count",[]]',
        'wss://namespace.method.dpays.io',
        4,
        4
    ),
    # namespace.method, params dict
    ({
        'id': 6027,
        'jsonrpc': '2.0',
        'method': 'namespace.method',
        'params': {'z': 'val1', 'a': [], 'f': 1}
    },
        {
        'namespace': 'namespace',
        'api': _empty,
        'method': 'method',
        'params': {'z': 'val1', 'a': [], 'f': 1}
    },
        'namespace.method.params={"a":[],"f":1,"z":"val1"}',
        'wss://namespace.method.dpays.io',
        4,
        4
    ),
    # namespace.method, no params
    ({
        'id': 6028,
        'jsonrpc': '2.0',
        'method': 'namespace.method',
    },
        {
        'namespace': 'namespace',
        'api': _empty,
        'method': 'method',
        'params': _empty
    },
        'namespace.method',
        'wss://namespace.method.dpays.io',
        4,
        4
    ),
    # namespace.method, empty params list
    ({
        'id': 6029,
        'jsonrpc': '2.0',
        'method': 'namespace.method',
        'params': []
    },
        {
        'namespace': 'namespace',
        'api': _empty,
        'method': 'method',
        'params': []
    },
        'namespace.method.params=[]',
        'wss://namespace.method.dpays.io',
        4,
        4
    ),
    # namespace.method, empty params dict
    ({
        'id': 6030,
        'jsonrpc': '2.0',
        'method': 'namespace.method',
        'params': {}
    },
        {
        'namespace': 'namespace',
        'api': _empty,
        'method': 'method',
        'params': {}
    },
        'namespace.method.params={}',
        'wss://namespace.method.dpays.io',
        4,
        4
    ),
    # namespace.method, params list
    ({
        'id': 6031,
        'jsonrpc': '2.0',
        'method': 'namespace.method',
        'params': [666]
    },
        {
        'namespace': 'namespace',
        'api': _empty,
        'method': 'method',
        'params': [666]
    },
        'namespace.method.params=[666]',
        'wss://namespace.method.params666.dpays.io',
        4,
        4
    ),
    # namespace.method, empty params dict
    ({
        'id': 6032,
        'jsonrpc': '2.0',
        'method': 'namespace.method',
        'params': {'key': 'value'}
    },
        {
        'namespace': 'namespace',
        'api': _empty,
        'method': 'method',
        'params': {'key': 'value'}
    },
        'namespace.method.params={"key":"value"}',
        'wss://namespace.method.dpays.io',
        4,
        4
    ),

    # -------NAMESPACE.API.METHOD-------------
    # namespace.api.method, no params
    ({
        'id': 7033,
        'jsonrpc': '2.0',
        'method': 'namespace.api.method',
    },
        {
        'namespace': 'namespace',
        'api': 'api',
        'method': 'method',
        'params': _empty
    },
        'namespace.api.method',
        'wss://namespace.api.method.dpays.io',
        5,
        5
    ),

    # namespace.api.method, empty params list
    ({
        'id': 7034,
        'jsonrpc': '2.0',
        'method': 'namespace.api.method',
        'params': []
    },
        {
        'namespace': 'namespace',
        'api': 'api',
        'method': 'method',
        'params': []
    },
        'namespace.api.method.params=[]',
        'wss://namespace.api.method.dpays.io',
        5,
        5
    ),

    # namespace.api.method, empty params dict
    ({
        'id': 7035,
        'jsonrpc': '2.0',
        'method': 'namespace.api.method',
        'params': {}
    },
        {
        'namespace': 'namespace',
        'api': 'api',
        'method': 'method',
        'params': {}
    },
        'namespace.api.method.params={}',
        'wss://namespace.api.method.dpays.io',
        5,
        5
    ),

    # namespace.api.method, params list
    ({
        'id': 7036,
        'jsonrpc': '2.0',
        'method': 'namespace.api.method',
        'params': [666]
    },
        {
        'namespace': 'namespace',
        'api': 'api',
        'method': 'method',
        'params': [666]
    },
        'namespace.api.method.params=[666]',
        'wss://namespace.api.method.params666.dpays.io',
        6,
        6
    ),

    # namespace.api.method, params dict
    ({
        'id': 7037,
        'jsonrpc': '2.0',
        'method': 'namespace.api.method',
        'params': {'key': '又遲到 了分'}
    },
        {
        'namespace': 'namespace',
        'api': 'api',
        'method': 'method',
        'params': {'key': '又遲到 了分'}
    },
        'namespace.api.method.params={"key":"又遲到 了分"}',
        'wss://namespace.api.method.dpays.io',
        5,
        5
    )

]

VALID_BROADCAST_TRANSACTIONS = [
    {
        'id': "24001",
        'jsonrpc': '2.0',
        'method': 'call',
        'params': [
            'condenser_api',
            'broadcast_transaction_synchronous',
            [
                {'expiration': '2018-04-23T22:40:21',
                 'extensions': [],
                 'operations': [
                     [
                         'custom_json',
                         {
                             "required_auths": [],
                             "id": "follow",
                             "json": "{\"follower\":\"jared\",\"following\":\"stan\",\"what\":[\"posts\"]}",
                             "required_posting_auths": ["jared"]
                         }
                     ]
                 ]
                 }
            ]
        ]
    },
    {
        'id': "24001",
        'jsonrpc': '2.0',
        'method': 'call',
        'params': [
            'condenser_api',
            'broadcast_transaction_synchronous',
            [
                {'expiration': '2018-04-23T22:40:21',
                 'extensions': [],
                 'operations': [
                     [
                         'custom_json',
                         {
                             "required_auths": [],
                             "id": "follow",
                             "json": "{\"follower\":\"jared\",\"following\":\"stan\",\"what\":[\"posts\"]}",
                             "required_posting_auths": ["jared"]
                         }
                     ]
                 ]
                 }
            ]
        ]
    },
    {
        'id': "24001",
        'jsonrpc': '2.0',
        'method': 'network_broadcast_api.broadcast_transaction_synchronous',
        'params': {
            'trx': {
                'expiration': '2018-04-23T22:40:21',
                'extensions': [],
                'operations': [
                    [
                        'custom_json',
                        {
                            "required_auths": [],
                            "id": "follow",
                            "json": "{\"follower\":\"jared\",\"following\":\"stan\",\"what\":[\"posts\"]}",
                            "required_posting_auths": ["jared"]
                        }
                    ]
                ]
            }

        }
    }
]

INVALID_BROADCAST_TRANSACTIONS = [
    {
        'id': "24001",
        'jsonrpc': '2.0',
        'method': 'call',
        'params': [
            'condenser_api',
            'broadcast_transaction_synchronous',
            [
                {'expiration': '2018-04-23T22:40:21',
                 'extensions': [],
                 'operations': [
                     [
                         'custom_json',
                         {
                             "required_auths": [],
                             "id": "follow",
                             "json": 'a' * 2001,
                             "required_posting_auths": ["jared"]
                         }
                     ]
                 ]
                 }
            ]
        ]
    },
    {
        'id': "24001",
        'jsonrpc': '2.0',
        'method': 'call',
        'params': [
            'condenser_api',
            'broadcast_transaction_synchronous',
            [
                {'expiration': '2018-04-23T22:40:21',
                 'extensions': [],
                 'operations': [
                     [
                         'custom_json',
                         {
                             "required_auths": [],
                             "id": "follow",
                             "json": "{\"follower\":\"jared\",\"following\":\"stan\",\"what\":[\"posts\"]}",
                             "required_posting_auths": ["non-dsite"]
                         }
                     ]
                 ]
                 }
            ]
        ]
    },
    {
        'id': "24001",
        'jsonrpc': '2.0',
        'method': 'network_broadcast_api.broadcast_transaction_synchronous',
        'params': {
            'trx':
                {'expiration': '2018-04-23T22:40:21',
                 'extensions': [],
                 'operations': [
                     [
                         'custom_json',
                         {
                             "required_auths": [],
                             "id": "follow",
                             "json": "{\"follower\":\"jared\",\"following\":\"stan\",\"what\":[\"posts\"]}",
                             "required_posting_auths": ["non-dsite"]
                         }
                     ]
                 ]
                 }
        }

    },
    {
        'id': "24001",
        'jsonrpc': '2.0',
        'method': 'network_broadcast_api.broadcast_transaction_synchronous',
        'params': {
            'trx':
                {
                    'expiration': '2018-04-23T22:40:21',
                    'extensions': [],
                    'operations': [
                        [
                            'custom_json',
                            {
                                "required_auths": [],
                                "id": "follow",
                                "json": 'a' * 2001,
                                "required_posting_auths": ["jared"]
                            }
                        ]
                    ]
                }
        }

    }
]


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def build_mocked_cache():
    mock_client = MockClient(cache=SimplerMaxTTLMemoryCache())
    return Cache(client=mock_client)


def make_request(headers: dict=None, body=None, app=None, method: str='POST',
                 url_bytes: bytes=b'/', upstreams=TEST_UPSTREAM_CONFIG) -> HTTPRequest:
    headers = headers or {'x-amzn-trace-id': '123', 'x-jefferson-request-id': '123'}
    if not app:
        app = sanic.Sanic('testApp')
        app.config.upstreams = _Upstreams(upstreams, validate=False)
    req = HTTPRequest(url_bytes, headers, '1.1', method, 'tcp')
    req.app = app

    if isinstance(body, dict):
        req.body = ujson.dumps(body, ensure_ascii=False).encode('utf8')
    else:
        req.body = body
    return req


@pytest.fixture(scope='session')
def upstreams():
    yield copy.deepcopy(_Upstreams(TEST_UPSTREAM_CONFIG, validate=False))


@pytest.fixture(scope='session')
def translate_to_appbase_upstreams():
    upstreams = copy.deepcopy(_Upstreams(TEST_UPSTREAM_CONFIG, validate=False))
    upstreams[0]['translate_to_appbbase'] = True
    yield upstreams


@pytest.fixture(scope='function')
def app(loop):
    args = jefferson.serve.parse_args(args=[])
    upstream_config_path = os.path.abspath(
        os.path.join(CONFIGS_DIR, 'TEST_UPSTREAM_CONFIG.json'))
    args.upstream_config_file = upstream_config_path
    args.test_upstream_urls = False
    # run app
    app = sanic.Sanic('testApp', request_class=HTTPRequest)
    app.config.args = args
    app.config.args.server_port = 42101
    app.config.args.websocket_pool_minsize = 0
    app.config.args.websocket_pool_maxsize = 1
    app = jefferson.logging_config.setup_logging(app)
    app = jefferson.serve.setup_routes(app)
    app = jefferson.middlewares.setup_middlewares(app)
    app = jefferson.errors.setup_error_handlers(app)
    app = jefferson.listeners.setup_listeners(app)

    try:
        loop.run_until_complete(app.config.cache_group.clear())
    except BaseException:
        pass

    yield app

    try:
        loop.run_until_complete(app.config.cache_group.clear())
    except BaseException:
        pass

    del app.config


@pytest.fixture(scope='function')
def app_without_ws(app):
    for i, l in enumerate(app.listeners['before_server_start']):
        if 'websocket' in str(l.__name__):
            del app.listeners['before_server_start'][i]
    for i, l in enumerate(app.listeners['after_server_stop']):
        if 'websocket' in str(l.__name__):
            del app.listeners['after_server_stop'][i]
    yield app


@pytest.fixture
def test_cli(app, loop, test_client):
    return loop.run_until_complete(test_client(app))


@pytest.fixture(scope='function')
def mocked_app_test_cli(app, loop, test_client):
    with asynctest.patch('jefferson.ws.pool.Pool._get_new_connection') as mocked_connect:
        mocked_ws_conn = asynctest.CoroutineMock()

        mocked_ws_conn.send = asynctest.CoroutineMock()
        mocked_ws_conn.send.return_value = None

        mocked_ws_conn.recv = asynctest.CoroutineMock()

        mocked_ws_conn.close = asynctest.CoroutineMock()
        mocked_ws_conn.close.return_value = None

        mocked_ws_conn.close_connection = asynctest.CoroutineMock()

        mocked_ws_conn.fail_connection = asynctest.MagicMock()
        mocked_ws_conn.fail_connection.return_value = None

        mocked_ws_conn.worker_task = asynctest.MagicMock()

        mocked_ws_conn.messages = asynctest.MagicMock()
        mocked_ws_conn.messages.qsize.return_value = 0
        mocked_ws_conn.messages.maxsize.return_value = 1
        mocked_ws_conn.messages._unfinished_tasks.return_value = 0
        mocked_ws_conn.messages.empty.return_value = True
        mocked_ws_conn._stream_reader = asynctest.MagicMock()
        mocked_connect.return_value = mocked_ws_conn

        initialized_client = loop.run_until_complete(test_client(app))
        yield mocked_ws_conn, initialized_client


@pytest.fixture(
    scope='function',
    params=['/', '/health', '/.well-known/healthcheck.json'])
def healthcheck_path(request):
    return request.param


@pytest.fixture
def healthcheck_url(jefferson_url, healthcheck_path):
    return f'{jefferson_url}{healthcheck_path}'


@pytest.fixture
def jrpc_request_validator(jrpc_request_schema):
    return rpartial(jsonschema.validate, jrpc_request_schema)


@pytest.fixture
def jrpc_response_validator(jrpc_response_schema):
    return rpartial(jsonschema.validate, jrpc_response_schema)


@pytest.fixture
def dpayd_jrpc_response_validator(dpayd_response_schema):
    return rpartial(jsonschema.validate, dpayd_response_schema)


@pytest.fixture(params=it.chain(tests.data.jsonrpc.invalid.requests,
                                tests.data.jsonrpc.invalid.batch))
def invalid_jrpc_single_and_batch_request(request):
    yield copy.deepcopy(request.param)


@pytest.fixture(
    scope='function', params=combined_requests_and_responses(),
    ids=lambda reqresp: str(URN(*reqresp[0])))
def combined_request_and_response(request):
    yield copy.deepcopy(request.param[0]), copy.deepcopy(request.param[1])


@pytest.fixture(params=DPAYD_JSONRPC_CALL_PAIRS)
def dpayd_method_pairs(request):
    yield request.param


@pytest.fixture(
    scope='function', params=dpayd_requests_and_responses(),
    ids=lambda reqresp: str(URN(*reqresp[0])))
def dpayd_request_and_response(request):
    yield copy.deepcopy(request.param[0]), copy.deepcopy(request.param[1])


@pytest.fixture(
    scope='function', params=appbase_requests_and_responses(),
    ids=lambda reqresp: str(URN(*reqresp[0])))
def appbase_request_and_response(request):
    yield copy.deepcopy(request.param[0]), copy.deepcopy(request.param[1])


@pytest.fixture(
    scope='function',
    params=it.chain(appbase_requests_and_responses(),
                    batched_appbase_requests_and_responses()),
    ids=lambda reqresp: str(URN(*reqresp[0])))
def appbase_request_and_response_single_and_batch(request):
    yield copy.deepcopy(request.param[0]), copy.deepcopy(request.param[1])


@pytest.fixture(params=translatable_dpayd_requests_and_responses())
def translatable_dpayd_request_and_response(request):
    yield copy.deepcopy(request.param)


@pytest.fixture(params=LONG_REQUESTS)
def long_request(request):
    yield request.param


@pytest.fixture(params=batch_translatable_requests_and_responses(15))
def batch_translatable_request_and_response(request):
    yield request.param


@pytest.fixture(params=batch_combined_requests(15))
def batch_combined_request(request):
    yield request.param


@pytest.fixture(params=URN_TEST_REQUEST_DICTS)
def full_urn_test_request_dict(request):
    yield copy.deepcopy(request.param)


@pytest.fixture(params=URN_TEST_REQUEST_DICTS)
def urn_test_request_dict(request):
    jsonrpc_request, urn_parsed, urn, url, ttl, timeout = request.param
    yield jsonrpc_request, urn, url, ttl, timeout


@pytest.fixture()
def urn_test_requests(urn_test_request_dict):
    jsonrpc_request, urn, url, ttl, timeout = urn_test_request_dict
    dummy_request = make_request()
    jefferson_request = jsonrpc_from_request(dummy_request, 0, jsonrpc_request)
    yield (jsonrpc_request,
           urn,
           url,
           ttl,
           timeout,
           jefferson_request
           )


@pytest.fixture
def dpayd_jefferson_request_and_dict(dpayd_request_and_response):
    jsonrpc_request, _ = dpayd_request_and_response
    dummy_request = make_request()

    jefferson_request = jsonrpc_from_request(dummy_request, 0,
                                         jsonrpc_request)
    yield (jefferson_request, jsonrpc_request)


@pytest.fixture(params=VALID_BROADCAST_TRANSACTIONS)
def valid_broadcast_transaction(request):
    yield copy.deepcopy(request.param)


@pytest.fixture(params=INVALID_BROADCAST_TRANSACTIONS)
def invalid_broadcast_transaction(request):
    yield copy.deepcopy(request.param)

# ---------------- DOCKER ------------------


def is_responsive(url):
    """Check if something responds to ``url``."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope='session')
def jefferson_docker_service(docker_ip, docker_services):
    """Ensure that "some service" is up and responsive."""
    url = 'http://%s:%s' % (docker_ip, docker_services.port_for('jefferson', 8080))
    print(url)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1,
        check=lambda: is_responsive(url)
    )
    return url


@pytest.fixture(scope='session')
def requests_session():
    session = requests.Session()
    return session


@pytest.fixture(scope='session')
def prod_url():
    return 'https://api.dpays.io'


@pytest.fixture
def sanic_server(loop, app, test_server):
    return loop.run_until_complete(test_server(app))
