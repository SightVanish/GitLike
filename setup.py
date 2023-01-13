#!/usr/bin/env python3
from setuptools import setup
'''
Install via `pip install -e .`, uninstall via `pip uninstall ugit -y`.
'''
setup(
        name='ugit',
        version='0.1',
        description="A simple version of Git",
        author="Wuchen",
        author_email="",
        packages=['ugit'],
        install_requires=[],
        entry_points={
                'console_scripts': [
                        'ugit = ugit.cli:main'
                ]
        }
)

