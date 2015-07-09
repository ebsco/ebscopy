from setuptools import setup, find_packages
import re

# README.md is used as the long description by default
ld_md								= open('README.md').read()

# If pandoc is installed and working, we can translate README.md directly to reStructuredText and use it for the long description
try:
	import pandoc
	pandoc.core.PANDOC_PATH			= '/usr/bin/pandoc'

	# Pandoc chokes on Unicode characters, which are used in the pronuncation guide
	ld_md							= re.sub("\(\*.*\*\)", "(*/'ebskOu,pai/*, not */'ebskopi:/*)", ld_md, re.M)

	doc								= pandoc.Document()
	doc.markdown					= ld_md
	ld								= doc.rst
except:
	ldw								= ld_md
# End of pandoc README translation attempt

# Regular setup data
setup(
	name							= 'ebscopy',
	version							= '0.0.4',
	author							= 'Jesse Jensen',
	author_email					= 'jjensen@ebsco.com',
	url								= 'https://github.com/jessejensen/ebscopy',
	license							= 'GNUv3',
	packages						= find_packages(),
	include_package_data			= True,
	description						= 'Official Python wrapper for the EBSCO Discovery Service (EDS) API',
	long_description				= ld,
	install_requires				= [
										"datetime",
										"json",
										"logging",
										"os",
										"pkg_resources",
										"re",
										"requests",
										"unittest",
									],
)

# EOF
