#!/usr/bin/env python3.8
"""Base API Client: Utils
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
from typing import NoReturn, Optional, Union


def bprint(message) -> NoReturn:
    msg = f'\n▃▅▇█▓▒░۩۞۩ {message.center(58)} ۩۞۩░▒▓█▇▅▃\n'
    print(msg)


def tprint(results, top: Optional[Union[int, None]] = None) -> NoReturn:
    top_hdr = f'Top {top} ' if top else ''

    print(f'{top_hdr}Success Result{"s" if len(results.success) > 1 else ""}:')
    if top:
        print(*results.success[:top], sep='\n')
    else:
        print(*results.success, sep='\n')

    print(f'\n{top_hdr}Failure Result{"s" if len(results.failure) > 1 else ""}:')
    if top:
        print(*results.failure[:top], sep='\n')
    else:
        print(*results.failure, sep='\n')


if __name__ == '__main__':
    print(__doc__)
