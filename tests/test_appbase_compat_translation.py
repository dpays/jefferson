# -*- coding: utf-8 -*-
from jefferson.request.jsonrpc import JSONRPCRequest


def test_id_translation(dpayd_jefferson_request_and_dict):
    jefferson_request, jsonrpc_request = dpayd_jefferson_request_and_dict
    urn = jefferson_request.urn
    translated_request_dict = JSONRPCRequest.translate_to_appbase(jsonrpc_request, urn)
    assert translated_request_dict['id'] == jefferson_request.id


def test_jsonrpc_translation(dpayd_jefferson_request_and_dict):
    jefferson_request, jsonrpc_request = dpayd_jefferson_request_and_dict
    urn = jefferson_request.urn
    translated_request_dict = JSONRPCRequest.translate_to_appbase(jsonrpc_request, urn)
    assert translated_request_dict['jsonrpc'] == jefferson_request.jsonrpc


def test_jrpc_method_translation(dpayd_jefferson_request_and_dict):
    jefferson_request, jsonrpc_request = dpayd_jefferson_request_and_dict
    urn = jefferson_request.urn
    translated_request_dict = JSONRPCRequest.translate_to_appbase(jsonrpc_request, urn)
    assert translated_request_dict['method'] == 'call'


def test_params_api_translation(dpayd_jefferson_request_and_dict):
    jefferson_request, jsonrpc_request = dpayd_jefferson_request_and_dict
    urn = jefferson_request.urn
    translated_request_dict = JSONRPCRequest.translate_to_appbase(jsonrpc_request, urn)
    assert translated_request_dict['params'][0] == 'condenser_api'


def test_params_method_translation(dpayd_jefferson_request_and_dict):
    jefferson_request, jsonrpc_request = dpayd_jefferson_request_and_dict
    urn = jefferson_request.urn
    translated_request_dict = JSONRPCRequest.translate_to_appbase(jsonrpc_request, urn)
    assert translated_request_dict['params'][1] == jefferson_request.urn.method


def test_params_param_translation(dpayd_jefferson_request_and_dict):
    jefferson_request, jsonrpc_request = dpayd_jefferson_request_and_dict
    urn = jefferson_request.urn
    translated_request_dict = JSONRPCRequest.translate_to_appbase(jsonrpc_request, urn)
    if jefferson_request.urn.params is False:
        assert translated_request_dict['params'][2] == []
    else:
        assert translated_request_dict['params'][2] == jefferson_request.urn.params
