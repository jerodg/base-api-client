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
import logging
from asyncio import Semaphore
from json.decoder import JSONDecodeError
from ssl import create_default_context, Purpose
from typing import List, NoReturn, Optional, Union

import aiohttp as aio
import toml
import ujson
from multidict import MultiDict
from tenacity import after_log, before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from base_api_client.models import Results

logger = logging.getLogger(__name__)


# todo: test request(); all types


class BaseApiClient(object):
    HDR: dict = {'Content-Type': 'application/json; charset=utf-8'}
    SEM: int = 25  # This defines the number of parallel async requests to make.

    def __init__(self, cfg: Optional[Union[str, dict]] = None, sem: Optional[int] = None):
        self.sem: Semaphore = Semaphore(sem or self.SEM)
        self.header: Union[dict, None] = None
        self.proxy: Union[str, None] = None
        self.proxy_auth: Union[aio.BasicAuth, None] = None
        self.ssl: Union[str, None] = None

        if type(cfg) is dict:
            self.cfg = cfg
        elif type(cfg) is str:
            self.cfg = toml.load(cfg)
        elif cfg is None:
            self.cfg = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def load_config(self) -> NoReturn:
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

    @staticmethod
    async def request_debug(response: aio.ClientResponse) -> str:
        # todo: convert to template
        hdr = '\n\t\t'.join(f'{k}: {v}' for k, v in response.headers.items())
        try:
            j = ujson.dumps(await response.json(content_type=None))
            t = None
        except JSONDecodeError:
            j = None
            t = await response.text()

        return f'\nHTTP/{response.version.major}.{response.version.minor}, {response.method}-{response.status}[{response.reason}]' \
            f'\n\tRequest-URL: \n\t\t{response.url}\n' \
            f'\n\tHeader: \n\t\t{hdr}\n' \
            f'\n\tResponse-JSON: \n\t\t{j}\n' \
            f'\n\tResponse-TEXT: \n\t\t{t}\n'

    async def process_results(self, results: List[Union[dict, aio.ClientResponse]], data: Optional[str] = None) -> Results:
        res = Results(results)

        for r in res.results:
            if type(r) is aio.ClientResponse:  # failure
                logger.error(await self.request_debug(r))
                res.failure.append(await r.json(content_type=None, encoding='utf-8', loads=ujson.loads()))
            else:
                if data:
                    res.success.extend(r[data])
                elif type(r) is list:
                    res.success.extend(r)
                else:
                    res.success.append(r)

        res.cleanup()
        return res

    @retry(retry=retry_if_exception_type(aio.ClientError),
           wait=wait_random_exponential(multiplier=1.25, min=3, max=60),
           after=after_log(logger, logging.DEBUG),
           stop=stop_after_attempt(5),
           before_sleep=before_sleep_log(logger, logging.WARNING))
    async def request(self, method: str, end_point: str, session: aio.ClientSession,
                      data: Optional[dict] = None,
                      json: Optional[dict] = None,
                      params: Optional[Union[List[tuple], dict, MultiDict]] = None) -> Union[dict, aio.ClientResponse, str]:
        """Multi-purpose aiohttp request function
        Args:
            method (str): A valid HTTP Verb in [GET, POST]
            end_point (str): REST Endpoint; e.g. /devices/query
            session (aio.ClientSession):
            data (Optional[dict]):
            json (Optional[dict]):
            params (Optional[Union[List[tuple], dict, MultiDict]]):

        References:
            https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol#Request_methods

        Raises:
            NotImplementedError
        """

        async with self.sem:
            if method == 'get':
                response = await session.get(url=f'{self.cfg["URI"]["Base"]}/{end_point}',
                                             ssl=self.ssl,
                                             proxy=self.proxy,
                                             proxy_auth=self.proxy_auth,
                                             params=params)
            elif method == 'post':
                response = await session.post(url=f'{self.cfg["URI"]["Base"]}/{end_point}',
                                              ssl=self.ssl,
                                              proxy=self.proxy,
                                              proxy_auth=self.proxy_auth,
                                              data=data,
                                              json=json,
                                              params=params)
            else:
                raise NotImplementedError

            if 200 <= response.status <= 299:
                if response.headers['Content-Type'] == 'application/jwt':
                    return {'token': await response.text(encoding='utf-8'), 'token_type': 'Bearer'}
                elif response.headers['Content-Type'] == 'application/json':
                    return await response.json(encoding='utf-8', loads=ujson.loads)
                elif response.headers['Content-Type'] == 'text/plain; charset=utf-8':
                    return await response.text(encoding='utf-8')
                else:
                    logger.error(f'Content-Type: {response.headers["Content-Type"]}, not currently handled.')
                    raise NotImplementedError
            elif response.status == 502:
                return response
                # todo: handle proxy error?
            elif response.status == 503:
                raise aio.ClientError
            else:
                return response

    @staticmethod
    def process_params(kwargs) -> dict:
        return {k: v for k, v in kwargs.items() if v is not None}


if __name__ == '__main__':
    print(__doc__)
