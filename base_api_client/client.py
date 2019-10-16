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
from ssl import create_default_context, Purpose, SSLContext
from typing import List, NoReturn, Optional, Union
from uuid import uuid4

import aiohttp as aio
import diskcache as dc
import rapidjson
import toml
from multidict import MultiDict
from os import getenv
from tenacity import after_log, before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from base_api_client.models import Results

logger = logging.getLogger(__name__)


# todo: convert request debug to template
# todo: add envar override for config
# todo: self.header is not necessary; find others
# todo: session_config, ensure order of config; config_file -> Environment Variables -> session_config(dict)


class BaseApiClient(object):
    HDR: dict = {'Content-Type': 'application/json; charset=utf-8'}
    SEM: int = 15  # This defines the number of parallel requests to make.

    def __init__(self, cfg: Optional[Union[str, dict]] = None):
        self.auth: Union[aio.BasicAuth, None] = None
        self.cache: Union[dc.Cache, dc.FanoutCache, dc.Deque, dc.Index, None] = None
        self.debug: bool = False
        self.cfg: Union[dict, None] = None
        self.header: Union[dict, None] = None
        self.proxy: Union[str, None] = None
        self.proxy_auth: Union[aio.BasicAuth, None] = None
        self.sem: Union[Semaphore, None] = None
        self.session: Union[aio.ClientSession, None] = None
        self.ssl: Union[SSLContext, None] = None

        await self.__load_config(cfg=cfg)
        await self.session_config(session_config=cfg)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def __load_config(self, cfg: Union[str, dict]) -> NoReturn:
        """

        Args:
            cfg (Union[str, dict): str; path to config file [toml|json]
                                   dict; dictionary matching config example
                Values expressed in example config can be overridden by OS
                environment variables.

        Returns:
            (NoReturn)
        """
        if type(cfg) is dict:
            self.cfg = cfg
        elif type(cfg) is str:
            if cfg.endswith('.toml'):
                cfg = toml.load(cfg)
            elif cfg.endswith('.json'):
                cfg = rapidjson.loads(open(cfg).read(), ensure_ascii=False)
            else:
                logger.error(f'Unknown configuration file type: {cfg.split(".")[1]}\n-> Valid Types: .toml | .json')
                raise NotImplementedError

        env_cfg = {'Auth':    {'Username': getenv('Auth_Username'),
                               'Password': getenv('Auth_Password'),
                               'Header':   getenv('Auth_Header'),
                               'Token':    getenv('Auth_Token')},
                   'URI':     {'Base': getenv('URI_Base')},
                   'Options': {'CAPath':    getenv('Options_CAPath'),
                               'VerifySSL': getenv('Options_VerifySSL'),
                               'Debug':     getenv('Options_Debug'),
                               'SEM':       getenv('Options_SEM')},
                   'Proxy':   {'URI':      getenv('Proxy_URI'),
                               'Port':     getenv('Proxy_Port'),
                               'Username': getenv('Proxy_Username'),
                               'Password': getenv('Proxy_password')},
                   'Cache':   {'Path': getenv('Cache_Path'),
                               'Type': getenv('Cache_Type')}}

        if not cfg['URI'] or not env_cfg['URI']:
            logger.error('No configuration provided.')
            raise NotImplementedError

        if cfg:
            if username := cfg['Auth'].pop('Username', None):
                self.auth = aio.BasicAuth(login=username, password=cfg['Auth'].pop('Password', None))
            if env_username := env_cfg['Auth'].pop('Username', None):
                self.auth = aio.BasicAuth(login=env_username, password=env_cfg['Auth'].pop('Password', None))

            if debug := cfg['Options'].pop('Debug', False):
                self.debug = debug
            if env_debug := env_cfg['Options'].pop('Debug', False):
                self.debug = env_debug

            if header := cfg['Auth'].pop('Header', None):
                self.header = {**self.HDR, header: cfg['Auth'].pop('Token', None)}
            if env_header := env_cfg['Auth'].pop('Header', None):
                self.header = {**self.HDR, env_header: env_cfg['Auth'].pop('Token', None)}

            if proxy_uri := cfg['Proxy'].pop('URI', None):
                proxy_port = cfg['Proxy'].pop('Port', '')
                self.proxy = f'{proxy_uri}{":" if proxy_port else ""}{proxy_port}'
                self.proxy_auth = aio.BasicAuth(login=cfg['Proxy'].pop('Username', None),
                                                password=cfg['Proxy'].pop('Password', None))
            if env_proxy_uri := env_cfg['Proxy'].pop('URI', None):
                env_proxy_port = env_cfg['Proxy'].pop('Port', '')
                self.proxy = f'{env_proxy_uri}{":" if env_proxy_port else ""}{env_proxy_port}'
                self.proxy_auth = aio.BasicAuth(login=env_cfg['Proxy'].pop('Username', None),
                                                password=env_cfg['Proxy'].pop('Password', None))

            if sem := cfg['Options'].pop('SEM', None):
                self.sem = sem
            if env_sem := env_cfg['Options'].pop('SEM', None):
                self.sem = env_sem

            if ssl_path := cfg['Options'].pop('CAPath', None):
                self.ssl = create_default_context(purpose=Purpose.CLIENT_AUTH, capath=ssl_path)
            else:
                self.ssl = cfg['Options'].pop('VerifySSL', True)

            if env_ssl_path := env_cfg['Options'].pop('CAPath', None):
                self.ssl = create_default_context(purpose=Purpose.CLIENT_AUTH, capath=env_ssl_path)

            cache_type = cfg['Cache'].pop('Type', None)
            if ct := env_cfg['Cache'].pop('Type', None):
                cache_type = ct

            cache_path = cfg['Cache'].pop('Path', None)
            if cp := env_cfg['Cache'].pop('Path'):
                cache_path = cp

            if cache_type:
                if cache_type == 'cache':
                    self.cache = dc.Cache(cache_path)
                elif cache_type == 'fanout_cache':
                    self.cache = dc.FanoutCache(cache_path)
                elif cache_type == 'deque':
                    self.cache = dc.Deque(cache_path)
                elif cache_type == 'index':
                    self.cache = dc.Index(cache_path)
                else:
                    logger.error(f'Invalid cache type: {cache_type}\n->Must be one of: cache|fanout_cache|deque|index')
                    raise NotImplementedError

    async def session_config(self, session_config: dict) -> NoReturn:
        if self.session:
            await self.session.close()

        # Auth
        username = session_config['Auth'].pop('Username', None)
        if env_username := getenv('Auth_Username'):
            username = env_username
        password = session_config['Auth'].pop('Password', None)
        if env_password := getenv('Auth_Password'):
            password = env_password

        if username:
            auth = aio.BasicAuth(login=username, password=password)
        else:
            auth = None

        # Cookies; Can't be overwridden by env_vars; Must be a dict
        try:
            cookies = session_config['Cache']['Cookies']
        except (KeyError, TypeError):
            cookies = None

        # Cookie Jar
        cookie_jar = aio.CookieJar(unsafe=session_config['Options'].pop('CookieJar_Unsafe', None) or False)

        # Headers
        auth_hdr = session_config['Auth'].pop('Header', None)
        if env_hdr := getenv('Auth_Header'):
            auth_hdr = env_hdr

        auth_tkn = session_config['Auth'].pop('Token', None)
        if env_tkn := getenv('Auth_Token'):
            auth_tkn = env_tkn

        if auth_hdr and auth_tkn:
            hdrs = {**self.HDR, session_config['Auth']['Header']: session_config['Auth']['Token']}
        else:
            hdrs = self.HDR

        # JSON Serialize
        try:
            jsn = session_config['Options']['JSON_Serialize']
            if env_jsn := getenv('Options_JSONSerialize'):
                jsn = env_jsn
        except (KeyError, TypeError):
            jsn = rapidjson.dumps

        self.session = aio.ClientSession(auth=auth,
                                         cookies=cookies,
                                         cookie_jar=cookie_jar,
                                         headers=hdrs,
                                         json_serialize=jsn)

    @staticmethod
    async def request_debug(response: aio.ClientResponse) -> str:
        hdr = '\n\t\t'.join(f'{k}: {v}' for k, v in response.headers.items())
        try:
            j = rapidjson.dumps(await response.json(content_type=None), ensure_ascii=False)
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
        sort_field (Optional[str]): Top incident_level dictionary key to sort on
        sort_order (Optional[str]): Direction to sort ASC | DESC (any case)
            Performs generic sort if sort_field not specified.

        Returns:
            results (Results): """
        for result in results.data:
            rid = {'request_id': result['request_id']}
            status = result['response'].status

            try:
                if result['response'].headers['Content-Type'].startswith('application/jwt'):
                    response = {'token': await result['response'].text(encoding='utf-8'), 'token_type': 'Bearer'}
                elif result['response'].headers['Content-Type'].startswith('application/json'):
                    response = await result['response'].json(encoding='utf-8', loads=rapidjson.loads)
                elif result['response'].headers['Content-Type'].startswith('application/javascript'):
                    response = await result['response'].json(encoding='utf-8', loads=rapidjson.loads,
                                                             content_type='application/javascript')
                elif result['response'].headers['Content-Type'].startswith('text/javascript'):
                    response = await result['response'].json(encoding='utf-8', loads=rapidjson.loads,
                                                             content_type='text/javascript')
                elif result['response'].headers['Content-Type'].startswith('text/plain'):
                    response = {'text_plain': await result['response'].text(encoding='utf-8')}
                elif result['response'].headers['Content-Type'].startswith('text/html'):
                    response = {'text_html': await result['response'].text(encoding='utf-8')}
                else:
                    logger.error(f'Content-Type: {result["response"].headers["Content-Type"]}, not currently handled.')
                    raise NotImplementedError
            except KeyError as ke:  # This shouldn't happen too often.
                logger.warning(ke)
                response = {'text_plain': await result['response'].text(encoding='utf-8')}

            if 200 <= status <= 299:
                try:
                    d = response[data_key]
                    if type(d) is list:
                        data = [{**r, **rid} for r in d]
                    else:
                        data = response
                except (KeyError, TypeError):
                    if type(response) is list:
                        data = [{**r, **rid} for r in response]
                    else:
                        data = {**response, **rid}

                if type(data) is list:
                    results.success.extend(data)
                else:
                    results.success.append(data)

            elif status > 299:
                results.failure.append({**response, **rid})

        if cleanup:
            del results.data
            results.success = [dict(sorted({k: v for k, v in rec.items() if v is not None}.items())) for rec in results.success]

        if sort_order:
            sort_order = sort_order.lower()

        if sort_field:
            results.success.sort(key=lambda k: k[sort_field], reverse=True if sort_order == 'desc' else False)
        elif sort_order:
            results.success.sort(reverse=True if sort_order == 'desc' else False)

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

            if self.debug or debug:
                print(await self.request_debug(response))

            try:
                assert not response.status > 499
            except AssertionError:
                logger.error(self.request_debug(response))
                raise aio.ClientError

            return {'request_id': request_id, 'response': response}


if __name__ == '__main__':
    print(__doc__)
