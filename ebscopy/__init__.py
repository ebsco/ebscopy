# ebscopy

import logging 
from ebscopy import *
from config import *

logging.basicConfig(
			filename='/tmp/ebscopy.log',
			level=logging.DEBUG,
			format='%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s'
)

__version__ = '0.0.1'
__author__ = 'Jesse Jensen'


#EOF
