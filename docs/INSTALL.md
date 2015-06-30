# How to Install

## AWS Environment
1. Create an Amazon Machine Instance and log in
2. Create a `virtualenv`:

		$ virtualenv py279
		New python executable in py279/bin/python2.7
		Also creating executable in py279/bin/python
		Installing setuptools, pip...done. 
		$ 

3. Activate the `virtualenv`:

		$  . py279/bin/activate
		(py279)$ 

4. Use `pip` to install `ebscopy` (and its dependencies):

		(py279)$ pip install ebscopy
		Collecting https://pypi.python.org/packages/source/e/ebscopy/ebscopy-0.0.2.dev1.tar.gz#md5=249fdc8f2f39a4c04126ea1ed2ed9151
		  Downloading ebscopy-0.0.2.dev1.tar.gz
		Collecting docutils>=0.3 (from ebscopy==0.0.2.dev1)
		  Downloading docutils-0.12.tar.gz (1.6MB)
		Collecting requests (from ebscopy==0.0.2.dev1)
		  Downloading requests-2.7.0-py2.py3-none-any.whl (470kB)
		Collecting datetime (from ebscopy==0.0.2.dev1)
		  Downloading DateTime-4.0.1.zip (65kB)
		Collecting logging (from ebscopy==0.0.2.dev1)
		  Downloading logging-0.4.9.6.tar.gz (96kB)
		Collecting zope.interface (from datetime->ebscopy==0.0.2.dev1)
		  Downloading zope.interface-4.1.2.tar.gz (919kB)
		Collecting pytz (from datetime->ebscopy==0.0.2.dev1)
		  Downloading pytz-2015.4-py2.py3-none-any.whl (475kB)
		Requirement already satisfied (use --upgrade to upgrade): setuptools in ./py279/lib/python2.7/site-packages (from zope.interface->datetime->ebscopy==0.0.2.dev1)
		Installing collected packages: docutils, requests, zope.interface, pytz, datetime, logging, ebscopy
		  Running setup.py install for docutils
		  Running setup.py install for zope.interface
		  Running setup.py install for datetime
		  Running setup.py install for logging
		  Running setup.py install for ebscopy
		Successfully installed datetime-4.0.1 docutils-0.12 ebscopy-0.0.2.dev1 logging-0.4.9.6 pytz-2015.4 requests-2.7.0 zope.interface-4.1.2
		(py279)$ 

5. Create the environment file with connection info (use sample.ebscopy_env, if needed):

		(py279)$ vi .ebscopy_env
		export EDS_AUTH=user
		export EDS_USER=username
		export EDS_PASS=password
		export EDS_PROFILE=profile
		export EDS_ORG=org
		export EDS_GUEST=n
		export EDS_HIGHLIGHT=n
		export EDS_LOG_LEVEL=INFO
		~
		~

6. Source the environment file:

		(py279)$ . ~/.ebscopy_env
		(py279)$ 

7. Test:

		(py279)$ python          
		Python 2.7.9 (default, Apr  1 2015, 18:18:03) 
		[GCC 4.8.2 20140120 (Red Hat 4.8.2-16)] on linux2
		Type "help", "copyright", "credits" or "license" for more information.
		>>> import ebscopy
		>>> connection = ebscopy.Connection()
		>>> connection.connect()
		>>> results = connection.search("blue")
		>>> results.pprint()
				Title: Blue Is the Warmest Color.
		PLink: http://search.ebscohost.com/login.aspx?direct=true&site=eds-live&db=bsx&AN=94933496
		DbId: bsx
		An: 94933496
		...



