#!/usr/bin/python

from ebscopy import ebscopy
#from config import Mode
#from ebscopy import config
#import  ebscopy

connection	= ebscopy.Connection()
connection.connect()
results = connection.search("red")
print "---------------"
print results
print "---------------"
print 
connection.disconnect()


