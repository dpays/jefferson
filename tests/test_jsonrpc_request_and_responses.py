# -*- coding: utf-8 -*-

import json
import pytest

correct_get_block_1000_response = {
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


@pytest.mark.parametrize(
    'jsonrpc_request, expected',
    [
        (
            # single jsonrpc dpayd request
            dict(id=1, jsonrpc='2.0', method='get_block', params=[1000]),
            correct_get_block_1000_response
        ),
        # batch jsronrpc dpayd request
        (
            [
                dict(id=1, jsonrpc='2.0', method='get_block', params=[1000]),
                dict(id=1, jsonrpc='2.0', method='get_block', params=[1000])
            ],
            [correct_get_block_1000_response, correct_get_block_1000_response]
        ),
        (
            # single jsonrpc old-style dpayd requests
            dict(
                id=1,
                jsonrpc='2.0',
                method='call',
                params=['database_api', 'get_block', [1000]]),
            correct_get_block_1000_response
        ),
        (
            # batch jsonrpc old-style dpayd request
            [
                dict(
                    id=1,
                    jsonrpc='2.0',
                    method='call',
                    params=['database_api', 'get_block', [1000]]),
                dict(
                    id=1,
                    jsonrpc='2.0',
                    method='call',
                    params=['database_api', 'get_block', [1000]])
            ],
            [correct_get_block_1000_response, correct_get_block_1000_response]
        ),
        (
            # batch jsonrpc mixed-style dpayd request
            [
                dict(id=1, jsonrpc='2.0', method='get_block', params=[1000]),
                dict(id=1, jsonrpc='2.0', method='call', params=[
                     'database_api', 'get_block', [1000]])
            ],
            [correct_get_block_1000_response, correct_get_block_1000_response]
        )
    ])
async def dpayd_multi_format_requests(mocked_app_test_cli, jsonrpc_request, expected, dpayd_jrpc_response_validator, mocker):

    with mocker.patch('jefferson.handlers.random',
                      getrandbits=lambda x: 1) as mocked_rand:
        mocked_ws_conn, test_cli = mocked_app_test_cli
        mocked_ws_conn.recv.return_value = mocked_ws_conn.send.call_args.dumps(
            correct_get_block_1000_response)

        response = await test_cli.post('/', json=jsonrpc_request, headers={'x-jefferson-request-id': '1'})
        assert response.status == 200
        assert response.headers['Content-Type'] == 'application/json'
        json_response = await response.json()
        assert dpayd_jrpc_response_validator(json_response) is None
        assert json_response == expected


async def test_mocked_dpayd_calls(mocked_app_test_cli, dpayd_jrpc_response_validator, dpayd_request_and_response, mocker):
    compare_key_only_ids = (6, 48)
    jrpc_req, jrpc_resp = dpayd_request_and_response

    mocked_ws_conn, test_cli = mocked_app_test_cli
    mocked_ws_conn.recv.return_value = json.dumps(jrpc_resp)

    response = await test_cli.post('/', json=jrpc_req, headers={'x-jefferson-request-id': str(jrpc_req['id'])})
    assert response.status == 200
    assert response.headers['Content-Type'] == 'application/json'
    assert 'x-jefferson-cache-hit' not in response.headers
    json_response = await response.json()
    assert dpayd_jrpc_response_validator(json_response) is None
    assert 'error' not in json_response
    assert json_response['id'] == jrpc_req['id']
    if jrpc_req['id'] in compare_key_only_ids:
        if isinstance(json_response['result'], dict):
            assert json_response['result'].keys() == jrpc_resp['result'].keys()
        else:
            assert len(json_response['result']) == len(jrpc_resp['result'])
    else:
        assert json_response == jrpc_resp


def jrpc_response_with_updated_id(m, jrpc):
    jrpc['id'] = json.loads(m.send.call_args[0][0])['id']
    return json.dumps(jrpc)
