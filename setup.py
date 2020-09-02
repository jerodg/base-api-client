#!/usr/bin/env python3.8
"""Base API Client: Setup
Copyright © 2019-2020 Jerod Gawne <https://github.com/jerodg/>

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
import logging
import sys
from os.path import realpath
from typing import NoReturn

from setuptools import find_packages, setup

logger = logging.getLogger(__name__)


def readme() -> str:
    with open(realpath('./README.md')) as f:
        return f.read()


def main() -> NoReturn:
    setup(author_email='jerod@jerodg.dev',
          author='Jerod Gawne',
          classifiers=['Development Status :: 5 - Production/Stable',
                       'Environment :: Console',
                       'Intended Audience :: End Users/Desktop',
                       'Intended Audience :: Developers',
                       'Intended Audience :: System Administrators',
                       'License :: Other/Proprietary License',
                       'Natural Language :: English',
                       'Operating System :: MacOS :: MacOS X',
                       'Operating System :: Microsoft :: Windows',
                       'Operating System :: POSIX',
                       'Programming Language :: Python :: 3.8',
                       'Topic :: Utilities',
                       'Topic :: Internet',
                       'Topic :: Internet :: WWW/HTTP'],
          description='Base API Client Library',
          entry_points={'console_scripts': []},
          include_package_data=True,
          install_requires=['aiodns',
                            'aiofiles',
                            'aiohttp',
                            'cchardet',
                            'python-rapidjson',
                            'tenacity',
                            'toml'],
          keywords='base api client rest',
          license='Server Side Public License',
          long_description_content_type='text/markdown',
          long_description=readme(),
          name='base-api-client',
          package_data={'base-api-client': []},
          packages=find_packages(),
          project_urls={'Bugs':          'https://github.com/jerodg/base-api-client/issues',
                        'Documentation': 'https://jerodg.github.io/base-api-client',
                        'Funding':       'https://www.paypal.me/jerodgawne',
                        'Say Thanks!':   'https://saythanks.io/to/jerodg',
                        'Source':        'https://github.com/jerodg/base-api-client'},
          python_requires='>=3.8, <=3.9',
          setup_requires=['aiodns',
                          'aiofiles',
                          'aiohttp',
                          'cchardet',
                          'python-rapidjson',
                          'tenacity',
                          'toml'] + ['pytest-runner'] if {'pytest', 'test', 'ptr'}.intersection(sys.argv) else [],
          tests_require=['pytest', 'pytest-asyncio'],
          url='https://pypi.org/project/base-api-client/',
          version='0!0.12.5',
          zip_safe=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as excp:
        logger.exception(excp)
