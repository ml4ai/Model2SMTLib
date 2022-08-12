from setuptools import setup, find_packages
import sys
import os

setup(name='gromet2smtlib',
      version='0.1',
      description='Gromet to SMT-Lib converter',
      url='',
      author='Dan Bryce',
      author_email='dbryce@sift.net',
      license='MIT',
      packages=find_packages('src'),
      package_dir={'':'src'},
      install_requires=["pysmt"],
      tests_require=["unittest"],
      zip_safe=False
      )