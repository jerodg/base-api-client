#!/usr/bin/env python3.8
"""Base API Client: Test Test Print
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

from base_api_client import BaseApiClient, bprint, tprint


@pytest.mark.asyncio
async def test_request_debug():
    ts = time.perf_counter()

    # todo: fix data before committing (non-proprietary)
    res = [{'id':                    '2f46f070-cd73-4bba-9845-ce7c04d08f0a', 'name': 'W7WS110575464', 'state': 'Online',
            'agent_version':         '2.0.1520', 'policy': {'id': 'd9b23f37-616f-4fc9-9a34-2020d97fd43c', 'name': 'Default'},
            'date_first_registered': '2019-06-14T13:16:40', 'ip_addresses': ['10.1.3.112'], 'mac_addresses': ['00-0C-29-74-9E-7D']},
           {'id':                    'edcc2ef2-a8be-4230-9584-111f8896f1ed', 'name': '110132185', 'state': 'Offline',
            'agent_version':         '2.0.1520',
            'policy':                {'id': 'e240a4c5-cbca-4d45-bf71-8c2d3976fe6c', 'name': 'BLOCK ALL THE THINGS'},
            'date_first_registered': '2019-04-16T10:52:27', 'ip_addresses': ['10.230.14.52'],
            'mac_addresses':         ['34-17-EB-A3-AC-11']},
           {'id':                    '4f7f1c2f-df33-44e3-b2ff-bdd04ca48e63', 'name': 'MacBook Pro', 'state': 'Online',
            'agent_version':         '2.0.1520',
            'policy':                {'id': 'e240a4c5-cbca-4d45-bf71-8c2d3976fe6c', 'name': 'ALL THE THINGS'},
            'date_first_registered': '2019-04-03T21:25:23', 'ip_addresses': ['172.18.33.8'],
            'mac_addresses':         ['F0-18-98-6A-C3-42']},
           {'id':                    '46a172a1-2d87-4fce-88ef-f270002fb555', 'name': '10124027', 'state': 'Offline',
            'agent_version':         '2.0.1520',
            'policy':                {'id': 'e240a4c5-fbca-4d45-bf71-8c2d3976fe6c', 'name': 'BLOCK ALL THE THINGS'},
            'date_first_registered': '2019-03-27T21:46:38', 'ip_addresses': ['10.222.229.121'],
            'mac_addresses':         ['18-03-73-28-E9-B9']},
           {'id':                    '528068ce-e6cb-4755-827f-9eaa678c1e3d', 'name': '110003004', 'state': 'Online',
            'agent_version':         '2.0.1520',
            'policy':                {'id': 'e240a4c5-cbca-4d45-bf71-8c2d3976fe6c', 'name': 'ALL THE THINGS'},
            'date_first_registered': '2019-02-27T15:42:27', 'ip_addresses': ['10.229.21.28'],
            'mac_addresses':         ['00-10-18-4E-13-FC']}
           ]

    with BaseApiClient() as bac:
        bprint('Test: Test Print (All Results)')
        tprint(await bac.process_results(res))

        # Test top 3 (expecting 3 success)
        bprint('Test: Test Print (Top 3 Results)')
        tprint(await bac.process_results(res), top=3)

    bprint(f'-> Completed in {(time.perf_counter() - ts):f} seconds.')
