#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-managerie',
    version='0.0',
    author='Aarni Koskela',
    author_email='akx@iki.fi',
    packages=find_packages(include=('django_managerie', 'django_managerie*')),
    include_package_data=True,
    install_requires=['Django', 'wrapt'],
)
