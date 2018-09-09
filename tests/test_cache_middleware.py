# -*- coding: utf-8 -*-
import json


import pytest


req = {"id": 1, "jsonrpc": "2.0", "method": "get_dynamic_global_properties"}

expected_dpayd_response = {
    "id": 1,
    "result": {
        "id":0,
        "head_block_number":63392,
        "head_block_id":"0000f7a0af081b838a72686618c001d0eb78180f",
        "time":"2018-09-06T21:46:27",
        "current_witness":"dpay",
        "total_pow":"18446744073709551615",
        "num_pow_witnesses":0,
        "virtual_supply":"190176.000 BEX",
        "current_supply":"190176.000 BEX",
        "confidential_supply":"0.000 BEX",
        "current_bbd_supply":"0.000 BBD",
        "confidential_bbd_supply":"0.000 BBD",
        "total_vesting_fund_dpay":"1.000 BEX",
        "total_vesting_shares":"1.000000 VESTS",
        "total_reward_fund_dpay":"126784.000 BEX",
        "total_reward_shares2":"0",
        "pending_rewarded_vesting_shares":"0.000000 VESTS",
        "pending_rewarded_vesting_dpay":"0.000 BEX",
        "bbd_interest_rate":1000,
        "bbd_print_rate":10000,
        "maximum_block_size":131072,
        "current_aslot":25811729,
        "recent_slots_filled":"340282366920938463463374607431768211455",
        "participation_count":128,
        "last_irreversible_block_num":63371,
        "vote_power_reserve_rate":40,
        "current_reserve_ratio":200000000,
        "average_block_size":90,
        "max_virtual_bandwidth":"528482304000000000000"
    }
}

expected_response = {
    "id": 1,
    "jsonrpc": "2.0",
    "result": {
        "average_block_size": 90,
        "confidential_bbd_supply": "0.000 BBD",
        "confidential_supply": "0.000 BEX",
        "current_aslot": 25811729,
        "current_reserve_ratio": 200000000,
        "current_bbd_supply": "0.000 BBD",
        "current_supply": "190176.000 BEX",
        "current_witness": "dpay",
        "head_block_id": "0000f7a0af081b838a72686618c001d0eb78180f",
        "head_block_number": 63392,
        "id": 0,
        "last_irreversible_block_num": 63371,
        "max_virtual_bandwidth": "528482304000000000000",
        "maximum_block_size": 65536,
        "num_pow_witnesses": 0,
        "participation_count": 128,
        "pending_rewarded_vesting_shares": "0.000000 VESTS",
        "pending_rewarded_vesting_dpay": "0.000 BEX",
        "recent_slots_filled": "340282366920938463463374607431768211455",
        "bbd_interest_rate": 0,
        "bbd_print_rate": 10000,
        "time": "2018-09-06T21:46:27",
        "total_pow": 18446744073709551615,
        "total_reward_fund_dpay": "126784.000 BEX",
        "total_reward_shares2": "0",
        "total_vesting_fund_dpay": "1.000 BEX",
        "total_vesting_shares": "1.000000 VESTS",
        "virtual_supply": "190176.000 BEX",
        "vote_power_reserve_rate": 40
    }
}


@pytest.mark.live
async def test_cache_response_middleware(test_cli):
    response = await test_cli.post('/', json=req)
    assert await response.json() == expected_dpayd_response
    response = await test_cli.post('/', json=req)
    assert response.headers['x-jefferson-cache-hit'] == 'dpayd.database_api.get_dynamic_global_properties'


async def test_mocked_cache_response_middleware(mocked_app_test_cli):
    mocked_ws_conn, test_cli = mocked_app_test_cli
    mocked_ws_conn.recv.return_value = json.dumps(expected_response)
    response = await test_cli.post('/', json=req, headers={'x-jefferson-request-id': '1'})
    assert 'x-jefferson-cache-hit' not in response.headers
    assert await response.json() == expected_response

    response = await test_cli.post('/', json=req, headers={'x-jefferson-request-id': '1'})
    assert response.headers['x-jefferson-cache-hit'] == 'dpayd.database_api.get_dynamic_global_properties'
    assert await response.json() == expected_response
