#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-managerie',
    version='0.0',
    packages=find_packages(include=('django_managerie', 'django_managerie*')),
    install_requires=['Django'],
)
