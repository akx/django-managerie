#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-managerie',
    version='0.1',
    author='Aarni Koskela',
    author_email='akx@iki.fi',
    description='Expose Django management commands in the admin',
    include_package_data=True,
    install_requires=['Django', 'wrapt'],
    license='MIT',
    packages=find_packages(include=('django_managerie', 'django_managerie*')),
    url='https://github.com/akx/django-managerie',
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
