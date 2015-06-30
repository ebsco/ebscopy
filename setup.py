from setuptools import setup, find_packages

setup(
  name='ebscopy',
  version='0.0.2.dev2',
  author='Jesse Jensen',
  author_email='jjensen@ebsco.com',
  url='https://github.com/jessejensen/ebscopy',
  license='GNUv3',
  #packages=['ebscopy','ebscopy.test'],
  packages=find_packages(),
  include_package_data=True,
  description='Official Python wrapper for EBSCO Discovery Service (EDS) API',
  long_description=open('README.txt').read(),
  install_requires=[
			'docutils>=0.3',
			'requests',
			'datetime',
			'logging',
  ],
  package_data = {
			# If any package contains *.txt or *.rst files, include them:
			'': ['*.txt', '*.rst', 'scripts', 'docs', 'samples',],
  },
)


