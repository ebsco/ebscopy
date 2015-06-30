# ebscopy
(/ˈɛbskoʊˌpaɪ/, not /ˈɛbskɒpiː/)

The official Python wrapper for the EBSCO Discovery Service API.

# Usage
```python
import ebscopy

connection = ebscopy.Connection()
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
# Notes

# Links
* http://eds-api.ebscohost.com/Console
* http://edswiki.ebscohost.com/EBSCO_Discovery_Service_API_User_Guide

# Thanks
Thanks to:
* EBSCO Information Services
* Dave Edwards - for hiring me
* Ron Burns - for letting Dave hire me
* Eric Frierson - for showing me how the API works
* Nitin Arora - for making the case for a Python EDS API wrapper and writing the original PyEDS
