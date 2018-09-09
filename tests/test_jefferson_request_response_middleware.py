# -*- coding: utf-8 -*-
import sanic.response

from jefferson.middlewares.jefferson import finalize_jefferson_response
from jefferson.upstream import _Upstreams
from jefferson.request.http import HTTPRequest
from .conftest import TEST_UPSTREAM_CONFIG


req = {"id": "1", "jsonrpc": "2.0",
       "method": "get_block", "params": [1000]}
response = {
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


def test_request_id_in_response_headers():
    app = sanic.Sanic('testApp', request_class=HTTPRequest)

    @app.post('/post')
    def handler(r):
        return sanic.response.text('post')

    @app.get('/get')
    def handler(r):
        return sanic.response.text('get')

    @app.head('/head')
    def handler(r):
        return sanic.response.text('head')

    @app.options('/options')
    def handler(r):
        return sanic.response.text('options')

    app.config.upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    app.response_middleware.append(finalize_jefferson_response)

    _, response = app.test_client.get('/get')
    assert 'x-jefferson-request-id' in response.headers

    _, response = app.test_client.post('/post')
    assert 'x-jefferson-request-id' in response.headers

    _, response = app.test_client.head('/head')
    assert 'x-jefferson-request-id' in response.headers

    _, response = app.test_client.options('/options')
    assert 'x-jefferson-request-id' in response.headers


def test_jefferson_request_ids_equal():
    app = sanic.Sanic('testApp', request_class=HTTPRequest)

    @app.post('/post')
    def handler(r):
        return sanic.response.text('post')

    @app.get('/get')
    def handler(r):
        return sanic.response.text('get')

    @app.head('/head')
    def handler(r):
        return sanic.response.text('head')

    @app.options('/options')
    def handler(r):
        return sanic.response.text('options')

    app.config.upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    app.response_middleware.append(finalize_jefferson_response)

    _, response = app.test_client.get('/get',
                                      headers={
                                          'x-jefferson-request-id': '123456789012345'
                                      })
    assert response.headers['x-jefferson-request-id'] == '123456789012345'

    _, response = app.test_client.post('/post',
                                       headers={
                                           'x-jefferson-request-id': '123456789012345'
                                       })
    assert response.headers['x-jefferson-request-id'] == '123456789012345'

    _, response = app.test_client.head('/head',
                                       headers={
                                           'x-jefferson-request-id': '123456789012345'
                                       })
    assert response.headers['x-jefferson-request-id'] == '123456789012345'

    _, response = app.test_client.options('/options',
                                          headers={
                                              'x-jefferson-request-id': '123456789012345'
                                          })
    assert response.headers['x-jefferson-request-id'] == '123456789012345'


def test_response_time_in_response_headers():
    app = sanic.Sanic('testApp', request_class=HTTPRequest)

    @app.post('/post')
    def handler(r):
        return sanic.response.text('post')

    @app.get('/get')
    def handler(r):
        return sanic.response.text('get')

    @app.head('/head')
    def handler(r):
        return sanic.response.text('head')

    @app.options('/options')
    def handler(r):
        return sanic.response.text('options')

    app.config.upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    app.response_middleware.append(finalize_jefferson_response)
    _, response = app.test_client.post('/post')

    assert 'x-jefferson-response-time' in response.headers
    assert float(response.headers['x-jefferson-response-time']) > 0

    _, response = app.test_client.get('/get')
    assert 'x-jefferson-response-time' in response.headers
    assert float(response.headers['x-jefferson-response-time']) > 0

    _, response = app.test_client.head('/head')
    assert 'x-jefferson-response-time' in response.headers
    assert float(response.headers['x-jefferson-response-time']) > 0

    _, response = app.test_client.options('/options')
    assert 'x-jefferson-response-time' in response.headers
    assert float(response.headers['x-jefferson-response-time']) > 0


def test_urn_parts_in_post_response_headers():
    app = sanic.Sanic('testApp', request_class=HTTPRequest)

    @app.post('/post')
    def handler(r):
        _ = r.jsonrpc  # trigger lazy parsing
        return sanic.response.text('post')

    app.config.upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    app.response_middleware.append(finalize_jefferson_response)

    _, response = app.test_client.post('/post', json=req)
    assert 'x-jefferson-request-id' in response.headers
    assert response.headers['x-jefferson-namespace'] == 'dpayd', f'{response.headers}'
    assert response.headers['x-jefferson-api'] == 'database_api', f'{response.headers}'
    assert response.headers['x-jefferson-method'] == 'get_block', f'{response.headers}'
    assert response.headers['x-jefferson-params'] == '[1000]', f'{response.headers}'


def test_urn_parts_not_in_batch_response_headers():
    app = sanic.Sanic('testApp', request_class=HTTPRequest)

    @app.post('/post')
    def handler(r):
        _ = r.jsonrpc  # trigger lazy parsing
        return sanic.response.text('post')

    app.config.upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    app.response_middleware.append(finalize_jefferson_response)

    _, response = app.test_client.post('/post', json=[req, req])
    assert 'x-jefferson-request-namespace' not in response.headers
    assert 'x-jefferson-request-api' not in response.headers
    assert 'x-jefferson-request-method' not in response.headers
    assert 'x-jefferson-request-params' not in response.headers


def test_urn_parts_not_in_get_response_headers():
    app = sanic.Sanic('testApp', request_class=HTTPRequest)

    @app.get('/get')
    def handler(r):
        _ = r.jsonrpc  # trigger lazy parsing
        return sanic.response.text('get')

    app.config.upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    app.response_middleware.append(finalize_jefferson_response)

    _, response = app.test_client.get('/get')
    assert 'x-jefferson-request-namespace' not in response.headers
    assert 'x-jefferson-request-api' not in response.headers
    assert 'x-jefferson-request-method' not in response.headers
    assert 'x-jefferson-request-params' not in response.headers


def test_urn_parts_not_in_head_response_headers():
    app = sanic.Sanic('testApp', request_class=HTTPRequest)

    @app.head('/head')
    def handler(r):
        _ = r.jsonrpc  # trigger lazy parsing
        return sanic.response.text('head')

    app.config.upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    app.response_middleware.append(finalize_jefferson_response)

    _, response = app.test_client.head('/head')
    assert 'x-jefferson-request-namespace' not in response.headers
    assert 'x-jefferson-request-api' not in response.headers
    assert 'x-jefferson-request-method' not in response.headers
    assert 'x-jefferson-request-params' not in response.headers


def test_urn_parts_not_in_options_response_headers():
    app = sanic.Sanic('testApp', request_class=HTTPRequest)

    @app.options('/options')
    def handler(r):
        _ = r.jsonrpc  # trigger lazy parsing
        return sanic.response.text('options')

    app.config.upstreams = _Upstreams(TEST_UPSTREAM_CONFIG, validate=False)
    app.response_middleware.append(finalize_jefferson_response)

    _, response = app.test_client.options('/options')
    assert 'x-jefferson-request-namespace' not in response.headers
    assert 'x-jefferson-request-api' not in response.headers
    assert 'x-jefferson-request-method' not in response.headers
    assert 'x-jefferson-request-params' not in response.headers
