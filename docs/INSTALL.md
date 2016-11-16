# How to Install

## Create a `virtualenv`
```shell
$ virtualenv py279
New python executable in py279/bin/python2.7
Also creating executable in py279/bin/python
Installing setuptools, pip...done. 
$ 
```

## Activate the `virtualenv`
```shell
$  . py279/bin/activate
(py279)$ 
```

## Use `pip` to install `ebscopy` (and its dependencies)
```shell
(py279)$ pip install ebscopy
You are using pip version 6.0.8, however version 7.1.0 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.
Collecting ebscopy
  Downloading ebscopy-0.0.2.dev4.tar.gz
Collecting requests (from ebscopy)
  Downloading requests-2.7.0-py2.py3-none-any.whl (470kB)
    100% |################################| 471kB 648kB/s 
Collecting datetime (from ebscopy)
  Downloading DateTime-4.0.1.zip (65kB)
    100% |################################| 65kB 1.4MB/s 
Collecting logging (from ebscopy)
  Downloading logging-0.4.9.6.tar.gz (96kB)
    100% |################################| 98kB 4.1MB/s 
Collecting nose (from ebscopy)
  Downloading nose-1.3.7-py2-none-any.whl (154kB)
    100% |################################| 155kB 2.8MB/s 
Collecting zope.interface (from datetime->ebscopy)
  Downloading zope.interface-4.1.2.tar.gz (919kB)
    100% |################################| 921kB 519kB/s 
Collecting pytz (from datetime->ebscopy)
  Downloading pytz-2015.4-py2.py3-none-any.whl (475kB)
    100% |################################| 475kB 1.1MB/s 
Requirement already satisfied (use --upgrade to upgrade): setuptools in ./main/lib/python2.7/site-packages (from zope.interface->datetime->ebscopy)
Installing collected packages: pytz, zope.interface, nose, logging, datetime, requests, ebscopy

  Running setup.py install for zope.interface
    building 'zope.interface._zope_interface_coptimizations' extension
    gcc -pthread -fno-strict-aliasing -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -DNDEBUG -O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -I/usr/include/python2.7 -c src/zope/interface/_zope_interface_coptimizations.c -o build/temp.linux-x86_64-2.7/src/zope/interface/_zope_interface_coptimizations.o
    unable to execute 'gcc': No such file or directory
    ********************************************************************************
    WARNING:
            An optional code optimization (C extension) could not be compiled.
            Optimizations for this package will not be available!
    ()
    command 'gcc' failed with exit status 1
    ********************************************************************************
    Skipping installation of /home/test/main/lib64/python2.7/site-packages/zope/__init__.py (namespace package)
    Installing /home/test/main/lib64/python2.7/site-packages/zope.interface-4.1.2-py2.7-nspkg.pth

  Running setup.py install for logging
  Running setup.py install for datetime

  Running setup.py install for ebscopy
Successfully installed datetime-4.0.1 ebscopy-0.0.2.dev4 logging-0.4.9.6 nose-1.3.7 pytz-2015.4 requests-2.7.0 zope.interface-4.1.2
(py279)$ 
```

## Create the environment file with connection info 
Use sample.ebscopy_env, if needed.
```shell
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
```

## Source the environment file
```shell
(py279)$ . ~/.ebscopy_env
(py279)$ 
```

## Test
```shell
(py279)$ python          
```
```pycon
Python 2.7.9 (default, Apr  1 2015, 18:18:03) 
[GCC 4.8.2 20140120 (Red Hat 4.8.2-16)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import ebscopy
>>> s = ebscopy.Session()
>>> r = s.search("blue")
>>> r.pprint()
Search Results
---------------
Title: Blue. [electronic resource].
PLink: http://search.ebscohost.com/login.aspx?direct=true&site=eds-live&db=cat03706a&AN=uoc.7467976
DbId: cat03706a
An: uoc.7467976

Title: Blue : a novel.
PLink: http://search.ebscohost.com/login.aspx?direct=true&site=eds-live&db=cat03706a&AN=uoc.9965828
DbId: cat03706a
An: uoc.9965828
...
```

## Celebrate!
