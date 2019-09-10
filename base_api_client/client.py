#!/usr/bin/env python3.8
"""Base API Client
Copyright © 2019 Jerod Gawne <https://github.com/jerodg/>

This program is free software: you can redistribute it and/or modify
it under the terms of the Server Side Public License (SSPL) as
published by MongoDB, Inc., either version 1 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
SSPL for more details.

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

You should have received a copy of the SSPL along with this program.
If not, see <https://www.mongodb.com/licensing/server-side-public-license>."""

import json
import logging
from asyncio import Semaphore
from json.decoder import JSONDecodeError
from ssl import create_default_context, Purpose
from typing import List, NoReturn, Optional, Union
from uuid import uuid4

import aiohttp as aio
import toml
import ujson
from diskcache import Index
from multidict import MultiDict
from tenacity import after_log, before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from base_api_client.models import Results

logger = logging.getLogger(__name__)


class BaseApiClient(object):
    HDR: dict = {'Content-Type': 'application/json; charset=utf-8'}
    SEM: int = 15  # This defines the number of parallel async requests to make.

    def __init__(self, cfg: Optional[Union[str, dict]] = None,
                 sem: Optional[int] = None,
                 index_location: Optional[str] = None,
                 session_config: dict = {}):
        self.sem: Semaphore = Semaphore(sem or self.SEM)
        self.header: Union[dict, None] = None
        self.proxy: Union[str, None] = None
        self.proxy_auth: Union[aio.BasicAuth, None] = None
        self.ssl = None
        self.auth = None
        self.cfg: Union[dict, None] = None
        self.__load_config(cfg=cfg)
        self.session: aio.ClientSession = self.__session_config(session_config)

        if index_location:
            self.index = Index(index_location)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    def __load_config(self, cfg) -> NoReturn:
        if type(cfg) is dict:
            self.cfg = cfg
        elif type(cfg) is str:
            if cfg.endswith('.toml'):
                self.cfg = toml.load(cfg)
            elif cfg.endswith('.json'):
                self.cfg = ujson.loads(open(cfg).read(), ensure_ascii=False)
            else:
                logger.error(f'Unknown configuration file type: {cfg.split(".")[1]}\n-> Valid Types: .toml | .json')
                raise NotImplementedError
        elif cfg is None:
            self.cfg = None

        if self.cfg:
            proxy_uri = self.cfg['Proxy'].pop('URI', None)
            if proxy_uri:
                proxy_port = self.cfg['Proxy'].pop('Port')
                proxy_user = self.cfg['Proxy'].pop('Username')
                proxy_pass = self.cfg['Proxy'].pop('Password')
                self.proxy = f'{proxy_uri}:{proxy_port}'
                self.proxy_auth = aio.BasicAuth(login=proxy_user, password=proxy_pass)

            ssl_path = self.cfg['Options'].pop('CAPath', None)
            if ssl_path:
                self.ssl = create_default_context(purpose=Purpose.CLIENT_AUTH, capath=ssl_path)
            else:
                self.ssl = self.cfg['Options'].pop('VerifySSL', True)

            if self.cfg['Auth']:
                self.auth = aio.BasicAuth(login=self.cfg['Auth']['Username'], password=self.cfg['Auth']['Password'])

    def __session_config(self, session_config):
        try:
            hdrs = {**self.HDR, self.cfg['Auth']['Header']: self.cfg['Auth']['Token']}
        except (KeyError, TypeError):
            hdrs = self.HDR
        try:
            jsn = session_config['json_serialize']
        except (KeyError, TypeError):
            jsn = json.dumps
        try:
            cookies = session_config['cookies']
        except (KeyError, TypeError):
            cookies = None
        try:
            cookie_jar = session_config['cookie_jar']
        except (KeyError, TypeError):
            cookie_jar = None

        return aio.ClientSession(cookies=cookies,
                                 cookie_jar=cookie_jar,
                                 headers=hdrs,
                                 auth=self.auth,
                                 json_serialize=jsn)

    @staticmethod
    async def request_debug(response: aio.ClientResponse) -> str:
        # todo: convert to template
        hdr = '\n\t\t'.join(f'{k}: {v}' for k, v in response.headers.items())
        try:
            j = ujson.dumps(await response.json(content_type=None), ensure_ascii=False)
            t = None
        except JSONDecodeError:
            j = None
            t = await response.text()

        return f'\nHTTP/{response.version.major}.{response.version.minor}, {response.method}-{response.status}[{response.reason}]' \
               f'\n\tRequest-URL: \n\t\t{response.url}\n' \
               f'\n\tHeader: \n\t\t{hdr}\n' \
               f'\n\tResponse-JSON: \n\t\t{j}\n' \
               f'\n\tResponse-TEXT: \n\t\t{t}\n'

    async def process_results(self, results: Results,
                              data_key: Optional[str] = None,
                              cleanup: bool = False,
                              sort_field: Optional[str] = None,
                              sort_order: Optional[str] = None) -> Results:
        """Process Results from aio.ClientRequest(s)

        Args:
        results (List[Union[dict, aio.ClientResponse]]):
        success (List[dict]):
        failure (List[dict]):
        data_key (Optional[str]):
        cleanup (Optional[bool]): Default: True
            Removes raw results, Removes empty (None) keys, and Sorts Keys of each record.
        sort_field (Optional[str]): Top level dictionary key to sort on
        sort_order (Optional[str]): Direction to sort ASC | DESC (any case)
            Performs generic sort if sort_field not specified.

        Returns:
            res (Results): """
        for result in results.data:
            rid = {'request_id': result['request_id']}
            status = result['response'].status

            if result['response'].headers['Content-Type'].startswith('application/jwt'):
                response = {'token': await result['response'].text(encoding='utf-8'), 'token_type': 'Bearer'}

            elif result['response'].headers['Content-Type'].startswith('application/json'):
                response = await result['response'].json(encoding='utf-8', loads=ujson.loads)

            elif result['response'].headers['Content-Type'].startswith('text/javascript'):
                response = await result['response'].json(encoding='utf-8', loads=ujson.loads, content_type='text/javascript')

            elif result['response'].headers['Content-Type'].startswith('text/plain'):
                response = {'text_plain': await result['response'].text(encoding='utf-8')}

            elif result['response'].headers['Content-Type'].startswith('text/html'):
                response = {'text_html': await result['response'].text(encoding='utf-8')}

            else:
                logger.error(f'Content-Type: {result["response"].headers["Content-Type"]}, not currently handled.')
                raise NotImplementedError

            if status > 299:
                results.failure.append({**response, **rid})
            elif 200 <= status <= 299:
                if data_key:
                    try:
                        results.success.extend([{**r, **rid} for r in response[data_key]])
                    except TypeError:
                        results.success.extend(response)
                    except KeyError:
                        logger.error(f'Key: {data_key}, does not exist in response data.')
                        raise KeyError
                else:
                    results.success.append({**response, **rid})

        if cleanup:
            del results.data
            results.success = [dict(sorted({k: v for k, v in rec.items() if v is not None}.items())) for rec in results.success]

        if sort_order:
            sort_order = sort_order.lower()

        if sort_field:
            results.success.sort(key=lambda k: k[sort_field], reverse=True if sort_order == 'desc' else False)
        elif sort_order:
            results.success.sort(reverse=True if sort_order == 'desc' else False)

        # print('results_base:', results)
        # print('results_base_success:')
        # print(*results.success, sep='\n')
        return results

    @retry(retry=retry_if_exception_type(aio.ClientError),
           wait=wait_random_exponential(multiplier=1.25, min=3, max=60),
           after=after_log(logger, logging.DEBUG),
           stop=stop_after_attempt(5),
           before_sleep=before_sleep_log(logger, logging.WARNING))
    async def request(self, method: str, end_point: str,
                      request_id: Optional[str] = None,
                      data: Optional[dict] = None,
                      json: Optional[dict] = None,
                      params: Optional[Union[List[tuple], dict, MultiDict]] = None,
                      debug: Optional[bool] = False) -> dict:
        """Multi-purpose aiohttp request function
        Args:
            method (str): A valid HTTP Verb in [GET, POST]
            end_point (str): REST Endpoint; e.g. /devices/query
            request_id (str): Unique Identifier used to associate request with response
            data (Optional[dict]):
            json (Optional[dict]):
            params (Optional[Union[List[tuple], dict, MultiDict]]):
            debug (Optional[bool]):

        References:
            https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol#Request_methods

        Raises:
            NotImplementedError
        """
        if not request_id:
            request_id = uuid4().hex

        async with self.sem:
            if method == 'get':
                response = await self.session.get(url=f'{self.cfg["URI"]["Base"]}{end_point}',
                                                  ssl=self.ssl,
                                                  proxy=self.proxy,
                                                  proxy_auth=self.proxy_auth,
                                                  params=params)
            elif method == 'post':
                response = await self.session.post(url=f'{self.cfg["URI"]["Base"]}{end_point}',
                                                   ssl=self.ssl,
                                                   proxy=self.proxy,
                                                   proxy_auth=self.proxy_auth,
                                                   data=data,
                                                   json=json,
                                                   params=params)
            elif method == 'put':
                response = await self.session.put(url=f'{self.cfg["URI"]["Base"]}{end_point}',
                                                  ssl=self.ssl,
                                                  proxy=self.proxy,
                                                  proxy_auth=self.proxy_auth,
                                                  data=data,
                                                  json=json,
                                                  params=params)
            elif method == 'delete':
                response = await self.session.delete(url=f'{self.cfg["URI"]["Base"]}{end_point}',
                                                     ssl=self.ssl,
                                                     proxy=self.proxy,
                                                     proxy_auth=self.proxy_auth,
                                                     data=data,
                                                     json=json,
                                                     params=params)
            else:
                logger.error(f'Request-Method: {method}, not currently handled.')
                raise NotImplementedError

            if debug:
                print(await self.request_debug(response))

            try:
                assert not response.status > 499
            except AssertionError:
                logger.error(self.request_debug(response))
                raise aio.ClientError

            return {'request_id': request_id, 'response': response}


if __name__ == '__main__':
    print(__doc__)
