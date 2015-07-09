# ebscopy
(*/ˈɛbskoʊˌpaɪ/,* not /ˈ*ɛbskɒpiː/*)

The official Python wrapper for the EBSCO Discovery Service API.

# Usage
* Basic:

```python
import ebscopy

session = ebscopy.Session(user_id="user", password="pass", profile="profile", org="org", guest="n")
results = session.search("blue")

print("Total Hits: %s" % results.stat_total_hits)
results.pprint()

session.end()
```

* Advanced: [USAGE.md](docs/USAGE.md)

# Installation
* Basic:

```python
pip install ebscopy
```

* Advanced: [INSTALL.md](docs/INSTALL.md)

# Links
* [EBSCO Discovery](https://www.ebscohost.com/discovery)
* [EDS API Console](http://eds-api.ebscohost.com/Console)
* [EDS API Wiki](http://edswiki.ebscohost.com/EBSCO_Discovery_Service_API_User_Guide)

# Notes
* I use four-space tabs. Sorry if that offends anyone.

# Thanks
* [EBSCO Information Services](https://www.ebsco.com/)
* *Dave Edwards* - for hiring me
* *Ron Burns* - for letting Dave hire me
* *Eric Frierson* - for showing me how the API works
* *Nitin Arora* - for making the case for a Python EDS API wrapper and writing the original PyEDS
