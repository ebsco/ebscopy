#!/usr/bin/python

from ebscopy import ebscopy
#import pprint

connection	= ebscopy.Connection()
connection.connect()
results = connection.search("blue")
print "---------------"
print "Search Results"
print "---------------"
#pprint.pprint(results)
#print results
print "---------------"
results.pretty_print()
print "---------------"
print 
connection.disconnect()


