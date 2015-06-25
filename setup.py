try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup


setup(
  name='ebscopy',
  version='0.0.1dev',
  author='Jesse Jensen',
  packages=['ebscopy','ebscopy.test'],
  description='Official Python wrapper for EBSCO Discover Service (EDS) API',
  long_description=open('README.md').read(),
  install_requires=[
          'requests',
          'datetime',
          'logging',
      ],
)


