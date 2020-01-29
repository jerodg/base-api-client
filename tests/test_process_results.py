#!/usr/bin/env python3.8
"""Base API Client: Test Process Results
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
import asyncio
import time

import aiohttp as aio
import pytest
import rapidjson
from os import getenv

from base_api_client import BaseApiClient, bprint, Results, tprint


# todo: use autodidact test endpoint to test, rewrite to handle changes to function
@pytest.mark.asyncio
async def test_process_results():
    ts = time.perf_counter()
    bprint('Test: Process Results')

    async with BaseApiClient(cfg=f'{getenv("CFG_HOME")}/base_api_client.toml') as bac:
        async with aio.ClientSession(headers=bac.HDR, json_serialize=rapidjson.dumps) as session:
            tasks = [asyncio.create_task(bac.request(method='get',
                                                     end_point='http://www.omdbapi.com',
                                                     params={'apikey': '42da97d5', 't': 'Blade Runner'}))]
            results = Results(data=await asyncio.gather(*tasks))

        assert type(results) is Results
        assert results.success is not None
        assert not results.failure
        processed_results = await bac.process_results(results)
        tprint(processed_results)

    # todo: test arguments (data_key, cleanup, sort_field, sort_order)

    bprint(f'-> Completed in {(time.perf_counter() - ts):f} seconds.')
