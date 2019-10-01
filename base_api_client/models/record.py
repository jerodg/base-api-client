#!/usr/bin/env python3.8
"""Base API Client: Models.Record
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
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Record:
    """Generic Record"""

    def clear(self):
        for k, v in self.__dict__.items():
            self.__dict__[k] = None

    def dict(self, d: dict = None, sort_order: str = None, cleanup: bool = True) -> dict:
        """
        Args:
            d (Optional[dict]):
            sort_order (Optional[str]): ASC | DESC
            cleanup (Optional[bool]):

        Returns:
            d (dict):"""
        if not d:
            d = self.__dict__

        if cleanup:
            d = {k: v for k, v in d.items() if v is not None}

        if sort_order:
            d = sorted(d, key=d.__getitem__, reverse=True if sort_order.lower() == 'desc' else False)

        return d

    def load(self, **entries):
        """Populates dataclass"
        Notes:
            Only works on top-level dicts"""
        self.__dict__.update(entries)


if __name__ == '__main__':
    print(__doc__)
