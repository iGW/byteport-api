#!/usr/bin/env python
__author__ = 'hans'

from setuptools import setup

setup(name='Byteport API',
      version='2.0',
      description='Python Clients for Byteport (www.byteport.se)',
      author='Byteport developers',
      author_email='contact@byteport.se',
      url='https://github.com/iGW/byteport-api',
      packages=['byteport_client'],
      install_requires=[
            'pytz==2018.9',
            'stompest==2.3.0',
            'paho-mqtt==1.1'
      ]
)
