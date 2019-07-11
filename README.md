```
 ___                   _   ___ ___    ___ _ _         _   
| _ ) __ _ ___ ___    /_\ | _ \_ _|  / __| (_)___ _ _| |_ 
| _ \/ _` (_-</ -_)  / _ \|  _/| |  | (__| | / -_) ' \  _|
|___/\__,_/__/\___| /_/ \_\_| |___|  \___|_|_\___|_||_\__|
```                                                                                                   
![platform](https://img.shields.io/badge/platform-Linux/Unix/Windows-blue.svg)
![python](https://img.shields.io/badge/python-3.6/7/8%2B-blue.svg)
![license](https://img.shields.io/badge/license-SSPL-green.svg)
![98%](https://img.shields.io/badge/coverage-98%25-green.svg)

Base module for REST API clients.

## Installation
```bash
pip install base-api-client
```

## Basic Usage
This modules' primary use-case is inheritance from other REST API clients.

```python
from base_api_client.base_api_client import BaseApiClient

class SomeApiClient(BaseApiClient):
    def __init__(self):
        BaseApiClient.__init__()
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        BaseApiClient.__exit__(self, exc_type, exc_val, exc_tb)
```

## License

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
If not, see <https://www.mongodb.com/licensing/server-side-public-license>.
