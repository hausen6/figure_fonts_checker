# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    author="joe nishihara",
    packages=find_packages(),
    entry_points="""
    [console_scripts]
    figure_fonts_checker = figure_fonts_checker:main
    """)