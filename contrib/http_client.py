# -*- coding: utf-8 -*-
# pylint: disable=all
import json
import logging
import os
import socket
import time
from functools import partial
from functools import partialmethod
from urllib.parse import urlparse

import certifi
import urllib3
from urllib3.connection import HTTPConnection

logger = logging.getLogger(__name__)


CORRECT_BATCH_TEST_RESPONSE = '''
[{"id":1,"result":{"previous":"0000000000000000000000000000000000000000","timestamp":"2018-09-04T16:36:27","witness":"dpay","transaction_merkle_root":"0000000000000000000000000000000000000000","extensions":[],"witness_signature":"201522e89ede4eea643486772bb7cf5fd59224f0de226840124651dcb7a22251d772e1a8a953d7218eddf83618351f33ec401007713070b435253d44a3ad937db2","transactions":[],"block_id":"000000011b5056ef5b610531031204f173aef7a8","signing_key":"DWB88FC9nDFczSTfVxrzHvVe8ZuvajLHKikfJYWiKkNvrUebBovzF","transaction_ids":[]}},{"id":2,"result":{"previous":"000000011b5056ef5b610531031204f173aef7a8","timestamp":"2018-09-04T16:36:33","witness":"dpay","transaction_merkle_root":"0000000000000000000000000000000000000000","extensions":[],"witness_signature":"1f39a1540cb5853377aa40c051ebde3fcc5a7b96d5b0881ed71ff10b8fcb6844711ed4920954ac80626486e49ba9ade4844813746590ab092bfc7ab1bca6a071b5","transactions":[],"block_id":"00000002c4809dadc4e67ac65e57c9530ab16782","signing_key":"DWB88FC9nDFczSTfVxrzHvVe8ZuvajLHKikfJYWiKkNvrUebBovzF","transaction_ids":[]}}]
'''


class RPCError(Exception):
    pass


class RPCConnectionError(Exception):
    pass


def chunkify(iterable, chunksize=3000):
    i = 0
    chunk = []
    for item in iterable:
        chunk.append(item)
        i += 1
        if i == chunksize:
            yield chunk
            i = 0
            chunk = []
    if chunk:
        yield chunk


class SimpleDPayAPIClient(object):
    """Simple DPay JSON-HTTP-RPC API

        This class serves as an abstraction layer for easy use of the
        DPay API.

    Args:
      str: url: url of the API server
      urllib3: HTTPConnectionPool url: instance of urllib3.HTTPConnectionPool

    .. code-block:: python

    from dpds.client import SimpleDPayAPIClient
    rpc = SimpleDPayAPIClient("http://domain.com:port")

    any call available to that port can be issued using the instance
    via the syntax rpc.exec_rpc('command', (*parameters*). Example:

    .. code-block:: python

    rpc.exec('info')

    Returns:

    """
    # pylint: disable=too-many-arguments

    def __init__(self,
                 url=None,
                 num_pools=2,
                 max_size=10,
                 timeout=60,
                 retries=30,
                 pool_block=False,
                 tcp_keepalive=True,
                 **kwargs):
        url = url or os.environ.get('DPAYD_HTTP_URL',
                                    'https://greatchain.dpays.io')
        self.url = url
        self.hostname = urlparse(url).hostname
        self.return_with_args = kwargs.get('return_with_args', False)
        self.re_raise = kwargs.get('re_raise', False)
        self.max_workers = kwargs.get('max_workers', None)

        maxsize = max_size
        timeout = timeout
        retries = retries
        pool_block = pool_block
        tcp_keepalive = tcp_keepalive

        if tcp_keepalive:
            socket_options = HTTPConnection.default_socket_options + \
                [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1), ]
        else:
            socket_options = HTTPConnection.default_socket_options

        self.http = urllib3.poolmanager.PoolManager(
            num_pools=num_pools,
            maxsize=maxsize,
            block=pool_block,
            timeout=timeout,
            retries=retries,
            socket_options=socket_options,
            headers={'Content-Type': 'application/json'},
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())
        '''
            urlopen(method, url, body=None, headers=None, retries=None,
            redirect=True, assert_same_host=True, timeout=<object object>,
            pool_timeout=None, release_conn=None, chunked=False, body_pos=None,
            **response_kw)
        '''
        self.request = partial(self.http.urlopen, 'POST', url)

        _logger = logging.getLogger('urllib3')

    @staticmethod
    def json_rpc_body(name, *args, as_json=True, _id=None):
        _id = _id or int(time.time() * 1000000)
        body_dict = {"method": name, "params": args,
                     "jsonrpc": "2.0", "id": _id}
        if as_json:
            return json.dumps(body_dict, ensure_ascii=False).encode('utf8')
        return body_dict

    def exec(self, name, *args, re_raise=None, return_with_args=None):
        body = SimpleDPayAPIClient.json_rpc_body(name, *args)
        try:
            response = self.request(body=body)
        except Exception as e:
            if re_raise:
                raise e
            else:
                extra = dict(err=e, request=self.request)
                logger.info('Request error', extra=extra)
                self._return(
                    response=None,
                    args=args,
                    return_with_args=return_with_args)
        else:
            if response.status not in tuple([*response.REDIRECT_STATUSES,
                                             200]):
                logger.debug('non 200 response:%s', response.status)

            return self._return(
                response=response,
                args=args,
                return_with_args=return_with_args)

    def _return(self, response=None, args=None, return_with_args=None):
        return_with_args = return_with_args or self.return_with_args

        if not response:
            result = None
        elif response.status != 200:
            result = None
        else:
            try:
                response_json = json.loads(response.data.decode('utf-8'))
            except Exception as e:
                extra = dict(response=response, request_args=args, err=e)
                logger.info('failed to load response', extra=extra)
                result = None
            else:
                if 'error' in response_json:
                    error = response_json['error']
                    error_message = error.get(
                        'detail', response_json['error']['message'])
                    raise RPCError(error_message)

                result = response_json.get('result', None)
        if return_with_args:
            return result, args
        return result

    def exec_multi(self, name, params):
        body_gen = ({
            "method": name,
            "params": [str(i)],
            "jsonrpc": "2.0",
            "id": i
        } for i in params)
        for chunk in chunkify(body_gen):
            batch_json_body = json.dumps(
                chunk, ensure_ascii=False).encode('utf8')
            r = self.request(body=batch_json_body).read()
            print(r)
            batch_response = json.loads(
                self.request(body=batch_json_body).read())
            for i, resp in enumerate(batch_response):
                yield self._return(
                    response=resp,
                    args=batch_json_body[i]['params'],
                    return_with_args=True)

    def exec_batch(self, name, params):
        batch_requests = [{
            "method": name,
            "params": [str(i)],
            "jsonrpc": "2.0",
            "id": i
        } for i in params]
        for chunk in chunkify(batch_requests):
            batch_json_body = json.dumps(chunk).encode()
            r = self.request(body=batch_json_body)
            batch_response = json.loads(r.data.decode())
            for resp in batch_response:
                yield json.dumps(resp)

    def test_batch_support(self, url):
        batch_request = '[{"id":1,"jsonrpc":"2.0","method":"get_block","params":[1]},{"id":2,"jsonrpc":"2.0","method":"get_block","params":[1]}]'
        try:
            response = self.request(body=batch_request)
            return response.data.decode() == CORRECT_BATCH_TEST_RESPONSE
        except Exception as e:
            logger.error(e)
        return False

    get_block = partialmethod(exec, 'get_block')
