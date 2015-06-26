# ebscopy

import os
import logging 
from ebscopy import *
from config import *

log_levels			= {
					'DEBUG':	logging.DEBUG,
					'INFO':		logging.INFO,
					'WARNING':	logging.WARNING,
					'ERROR':	logging.ERROR,
					'CRITICAL':	logging.CRITICAL,
				}

if os.environ.get('EDS_LOG_LEVEL') in log_levels.keys():
  log_level			= log_levels[os.environ.get('EDS_LOG_LEVEL')]
else:
  log_level			= logging.NOTSET

logging.basicConfig(
			filename='/tmp/ebscopy.log',
			level=log_level,
			format='%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s'
)

__version__			= '0.0.1'
__author__			= 'Jesse Jensen'


#EOF
