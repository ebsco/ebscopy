from setuptools import setup, find_packages

setup(
  name='ebscopy',
  version='0.0.2.dev4',
  author='Jesse Jensen',
  author_email='jjensen@ebsco.com',
  url='https://github.com/jessejensen/ebscopy',
  license='GNUv3',
  packages=find_packages(),
  include_package_data=True,
  description='Official Python wrapper for the EBSCO Discovery Service (EDS) API',
  long_description=open('README.md').read(),
  install_requires=[
			'requests',
			'datetime',
			'logging',
			'nose',
  ],
  package_data = {
  },
)


