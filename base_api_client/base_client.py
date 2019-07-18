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
from typing import List, Optional, Union

import aiohttp as aio
import toml
import ujson

from base_api_client import Results

logger = logging.getLogger(__name__)


class BaseApiClient(object):
    SEM: int = 25  # This defines the number of parallel async requests to make.

    def __init__(self, cfg: Optional[Union[str, dict]] = None, sem: Optional[int] = None):
        self.sem: Semaphore = Semaphore(sem or self.SEM)
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

    @staticmethod
    async def request_debug(response: aio.ClientResponse) -> str:
        # todo: convert to template
        """Pretty Print Request-Response"""
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

    @staticmethod
    def process_params(kwargs) -> dict:
        return {k: v for k, v in kwargs.items() if v is not None}


if __name__ == '__main__':
    print(__doc__)
