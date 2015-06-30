try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup


setup(
  name='ebscopy',
  version='0.0.2.dev0',
  author='Jesse Jensen',
  author_email='jjensen@ebsco.com',
  url='https://github.com/jessejensen/ebscopy',
  packages=['ebscopy','ebscopy.test'],
  include_package_data=True,
  description='Official Python wrapper for EBSCO Discover Service (EDS) API',
  long_description=open('README.txt').read(),
  install_requires=[
          'requests',
          'datetime',
          'logging',
      ],
)


