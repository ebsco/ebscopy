from setuptools import setup, find_packages
import re

# README.md is used as the long description by default
ld							= ""
ld_md						= open('README.md').read()

# If pandoc is installed and working, we can translate README.md directly to reStructuredText and use it for the long description
try:
	import pypandoc
	pypandoc.PANDOC_PATH	= '/usr/bin/pandoc'

	# Pandoc chokes on Unicode characters, which are used in the pronuncation guide
	ld_md					= re.sub("\(\*.*\*\)", "(*/'ebskOu,pai/*, not */'ebskopi:/*)", ld_md, re.M)

	ld						= pypandoc.convert(ld_md, "rst", format="md")
except:
	ld						= ld_md
# End of pandoc README translation attempt

# Regular setup data
setup(
	name					= 'ebscopy',
	version					= '0.1.17',
	author					= 'Jesse Jensen',
	author_email			= 'jjensen@ebsco.com',
	url						= 'https://github.com/jessejensen/ebscopy',
	license					= 'GNUv3',
	packages				= find_packages(),
	include_package_data	= True,
	description				= 'Official Python wrapper for the EBSCO Discovery Service (EDS) API',
	long_description		= ld,
	install_requires		= [
								"datetime",
								"logging",
								"requests",
							],
	data_files				= [ 
								("ebscopy/samples", 
									["samples/sample.ebscopy_env", "samples/plain_old_test.py"]),
								 ("ebscopy/docs", 
									["docs/INSTALL.md", "docs/USAGE.md"]) 
							],
	classifiers				= [
								'Programming Language :: Python',
								'Development Status :: 3 - Alpha',
								'Natural Language :: English',
								'Intended Audience :: Education',
								'Intended Audience :: Developers',
								'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
								'Operating System :: OS Independent',
								'Topic :: Software Development :: Libraries',
								'Topic :: Software Development :: Libraries :: Python Modules',
								'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
								],
)

# EOF
