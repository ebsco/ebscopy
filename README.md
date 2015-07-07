# ebscopy
(*/ˈɛbskoʊˌpaɪ/,* not /ˈ*ɛbskɒpiː/*)

The official Python wrapper for the EBSCO Discovery Service API.

# Usage
```python
import ebscopy

connection = ebscopy.Connection(user_id="user", password="pass", profile="profile", org="org", guest="n")
connection.connect()
results = connection.search("blue")

print "Search Results"
print "---------------"
results.pprint()

print "Total Hits:"
print results.stat_total_hits

print "Available Facets:"
print results.avail_facets_labels

connection.disconnect()
```

# Installation
* See [INSTALL.md](docs/INSTALL.md)

# Links
* [EBSCO Discovery](https://www.ebscohost.com/discovery)
* [EDS API Console](http://eds-api.ebscohost.com/Console)
* [EDS API Wiki](http://edswiki.ebscohost.com/EBSCO_Discovery_Service_API_User_Guide)

# Thanks
* [EBSCO Information Services](https://www.ebsco.com/)
* *Dave Edwards* - for hiring me
* *Ron Burns* - for letting Dave hire me
* *Eric Frierson* - for showing me how the API works
* *Nitin Arora* - for making the case for a Python EDS API wrapper and writing the original PyEDS
