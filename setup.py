#/usr/bin/env python
import os
from setuptools import setup, find_packages

ROOT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(ROOT_DIR)

setup(
    name="python-markov",
    description="Some utility methods for generating and storing markov chains with python and redis",
    author="Grant Thomas",
    author_email="grant.thomas@wk.com",
    url="https://github.com/wieden-kennedy/python-markov",
    version="0.0.1",
    install_requires=["redis"],
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
