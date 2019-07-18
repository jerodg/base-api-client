#!/usr/bin/env python3.8
"""Base API Client: Test Process Params
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

import pytest

from base_api_client.base_client import BaseApiClient
from base_api_client.base_utils import bprint


@pytest.mark.asyncio
async def test_process_params():
    ts = time.perf_counter()
    bprint('Test: Process Params')

    with BaseApiClient() as bapi:
        params = {'key0': 'value0', 'key1': None}

        results = bapi.process_params(params)
        print('Results:\n', results)

        assert type(results) is dict

        try:
            key1 = results['key1']
        except KeyError:
            key1 = 'None'

        assert key1 == 'None'
        print('Results:\n', results)

    bprint(f'-> Completed in {(time.perf_counter() - ts):f} seconds.')
