# ebscopy

("EBSCO-PY", not "EBS-COPY")

(test)

The official Python wrapper for the EBSCO Discovery Service API.

# Usage

```python
import ebscopy

session = ebscopy.Session(user_id="user", password="pass", profile="profile", org="org", guest="n")
results = session.search("blue")

print("Total Hits: %s" % results.stat_total_hits)
results.pprint()

session.end()
```

-   More examples: [USAGE.md](docs/USAGE.md)
-   [~~Complete module documentation~~](http://ebscopy.readthedocs.org/en/latest/)

# Installation

```python
pip install ebscopy
```

-   More info: [INSTALL.md](docs/INSTALL.md)
-   [PYPI Page](https://pypi.python.org/pypi/ebscopy)

# Links

-   [EBSCO Discovery](https://www.ebscohost.com/discovery)
-   [EDS API Console](http://eds-api.ebscohost.com/Console)
-   [EDS API Wiki](http://edswiki.ebscohost.com/EBSCO_Discovery_Service_API_User_Guide)

# Notes

-   I use four-space tabs. Sorry if that offends anyone.

# Thanks

-   [EBSCO Information Services](https://www.ebsco.com/)
-   _Dave Edwards_ - for hiring me
-   _Ron Burns_ - for letting Dave hire me
-   _Eric Frierson_ - for showing me how the API works
-   _Nitin Arora_ - for making the case for a Python EDS API wrapper and writing the original PyEDS
