# -*- coding: utf-8 -*-
#
# LICENCE       MIT
#
# DESCRIPTION   Setup for callgraph package.
#
# AUTHOR        Michal Bukovsky <michal.bukovsky@trilogic.cz>
#

from setuptools import setup, find_packages

setup(name="callgraph",
      version="1.0.0",
      install_requires=["cached_property"],
      description="Build callgraph from statically reacheble code.",
      author="Michal Bukovsky",
      author_email="michal.bukovsky@trilogic.cz",
      packages=find_packages(exclude=["tests"]),
      test_suite="tests",
      licence="MIT")

