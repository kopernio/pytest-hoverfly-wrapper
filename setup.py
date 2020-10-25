#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="pytest-hoverfly-wrapper",
    version="0.4.0",
    author="Veli Akiner",
    author_email="veli@kopernio.com",
    maintainer="Veli Akiner",
    maintainer_email="veli@kopernio.com",
    license="MIT",
    url="https://github.com/kopernio/pytest-hoverfly-wrapper",
    description="Integrates the Hoverfly HTTP proxy into Pytest",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    python_requires=">=3.5",
    install_requires=["pytest>=3.7.0", "requests", "python-dateutil", "polling"],
    tests_require=["pytest-mock",],
    packages=["pytest_hoverfly_wrapper"],
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["hoverfly-wrapper = pytest_hoverfly_wrapper.plugin",],},
)
