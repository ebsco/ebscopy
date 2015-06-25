#!/usr/bin/python

from ebscopy import ebscopy

connection	= ebscopy.Connection()
connection.connect()
results = connection.search("red")
print "---------------"
print results
print "---------------"
print 
connection.disconnect()


