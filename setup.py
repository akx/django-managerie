import re
from setuptools import setup, find_packages

try:
    with open('./django_managerie/__init__.py', 'r') as infp:
        version = re.search("__version__ = ['\"]([^'\"]+)['\"]", infp.read()).group(1)
except IOError:
    version = 'unknown'


setup(
    name='django-managerie',
    version=version,
    author='Aarni Koskela',
    author_email='akx@iki.fi',
    description='Expose Django management commands in the admin',
    include_package_data=True,
    install_requires=['Django>=2.2', 'wrapt'],
    license='MIT',
    packages=find_packages(include=('django_managerie', 'django_managerie*')),
    url='https://github.com/akx/django-managerie',
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
