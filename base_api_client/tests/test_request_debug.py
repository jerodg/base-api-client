#!/usr/bin/env python3.8
"""Base API Client: Test Request Debug
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
import time

import aiohttp as aio
import pytest
from os import environ

from base_api_client.base_api_client import BaseApiClient
from base_api_client.base_api_utils import bprint


@pytest.mark.asyncio
async def test_request_debug():
    ts = time.perf_counter()
    bprint('Test: Request Debug')

    environ['HTTPS_PROXY'] = 'http://webgateway.info53.com:8080'

    with BaseApiClient() as bapi:
        async with aio.ClientSession(trust_env=True) as session:
            response = await session.get('https://pypi.org')

        results = await bapi.request_debug(response=response)

        assert type(results) is str

        print(results)

    bprint(f'-> Completed in {time.perf_counter() - ts} seconds.')
