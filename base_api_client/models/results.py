#!/usr/bin/env python3.8
"""Base API Client: Models.Results
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
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class Results:
    """Results from aio.ClientRequest(s)

    Attributes:
        data (List[dict]):
        success (List[dict]):
        failure (List[dict]):"""
    data: List[dict]
    success: List[dict] = field(default_factory=list)
    failure: List[dict] = field(default_factory=list)

    @property
    def dict(self) -> dict:
        return {'success': self.success, 'failure': self.failure}
