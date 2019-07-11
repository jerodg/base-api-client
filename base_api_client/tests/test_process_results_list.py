#!/usr/bin/env python3.8
"""Base API Client: Test Process Results List
Copyright © 2019 Jerod Gawne <https://github.com/jerodg/>

This program is free software: you can redistribute it and/or modify
it under the terms of the Server Side Public License (SSPL) as
published by MongoDB, Inc., either version 1 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
SSPL for more details.

You should have received a copy of the SSPL along with this program.
If not, see <https://www.mongodb.com/licensing/server-side-public-license>."""
import time

import pytest

from base_api_client.base_api_client import BaseApiClient
from base_api_client.base_api_utils import bprint


@pytest.mark.asyncio
async def test_process_results_list():
    ts = time.perf_counter()
    bprint('Test: Process Results List')

    with BaseApiClient() as bapi:
        raw_results = [{'key0': 'value0',
                        'key1': 'value1',
                        'data': [{'some_key': 'some_value', 'another_key': 'another_value'},
                                 {'some_key': 'some_value', 'another_key': 'another_value'}]}]

        results = await bapi.process_results(results=raw_results, data='data')
        # print(f'Results: {results}')

        assert type(results) is dict
        assert results['success'] is not None
        assert results['failure'][0] is None

        try:
            key0 = results['success'][0]['key0']
        except KeyError:
            key0 = 'None'

        assert key0 == 'None'

        print('Top 5 Success Results:')
        print(*results['success'][:5], sep='\n')
        print('\nTop 5 Failure Result:')
        print(*results['failure'][:5], sep='\n')

    bprint(f'-> Completed in {time.perf_counter() - ts} seconds.')
