#!/usr/bin/env python3.8
"""Base API Client: Setup
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
import logging
from typing import NoReturn

from setuptools import find_packages, setup

logger = logging.getLogger(__name__)


def readme() -> str:
    with open('README.md') as f:
        return f.read()


def main() -> NoReturn:
    setup(name='base-api-client',
          version='0!1.0b2.dev2',
          description='Base API Client Library',
          long_description=readme(),
          long_description_content_type='text/markdown',
          url='https://pypi.org/project/base-api-client/',
          author='Jerod Gawne',
          author_email='jerod@jerodg.dev',
          classifiers=['Development Status :: 4 - Beta',
                       'Intended Audience :: Developers',
                       'Topic :: Utilities',
                       'Topic :: Internet :: WWW/HTTP',
                       'Programming Language :: Python :: 3.6',
                       'Programming Language :: Python :: 3.7',
                       'Programming Language :: Python :: 3.8',
                       'License :: Other/Proprietary License',
                       'Natural Language :: English',
                       'Operating System :: MacOS :: MacOS X',
                       'Operating System :: Microsoft :: Windows',
                       'Operating System :: POSIX'],
          keywords='base api client rest',
          license='Server Side Public License (SSPL)',
          packages=find_packages(exclude=['docs', 'examples', 'tests']),
          python_requires='>=3.6, <3.9',
          install_requires=['aiodns', 'aiohttp', 'cchardet', 'toml', 'ujson'],
          extras_require={'dev':  [],
                          'test': []},
          package_data={'base-api-client': []},
          entry_points={'console_scripts': []},
          project_urls={'Documentation': 'https://jerodg.github.io/base-api-client',
                        'Source':        'https://github.com/jerodg/base-api-client',
                        'Bugs':          'https://github.com/jerodg/base-api-client/issues',
                        'Say Thanks!':   'https://saythanks.io/to/jerodg',
                        'Funding':       'Paypal: jerod@jerodg.dev'},
          include_package_data=True,
          zip_safe=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as excp:
        logger.exception(excp)
