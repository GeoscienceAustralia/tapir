#!/usr/bin/python3

from setuptools import setup

setup(
    name='tapir',
    version='0.0.1',
    description="GA AWS resilience library",
    author="The Geoscience Australia Autobots",
    author_email="autobots@ga.gov.au",
    url="https://github.com/GeoscienceAustralia/tapir",
    license="New BSD license",
    packages=['lambdas'],
    install_requires=[
        'nose',
        'boto3',
    ]
)
