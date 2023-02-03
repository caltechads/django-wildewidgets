#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="demo",
    version="0.15.1",
    description="",
    author="Caltech IMSS ADS",
    author_email="imss-ads-staff@caltech.edu",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "htmlcov"])
)
