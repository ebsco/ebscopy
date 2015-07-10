# ebscopy __init__

import os
import logging 
from ebscopy import *
from pkg_resources import get_distribution

log_levels									= {
												'DEBUG':	logging.DEBUG,
												'INFO':		logging.INFO,
												'WARNING':	logging.WARNING,
												'ERROR':	logging.ERROR,
												'CRITICAL':	logging.CRITICAL,
												}

if os.environ.get('EDS_LOG_LEVEL') in log_levels.keys():
	log_level								= log_levels[os.environ.get('EDS_LOG_LEVEL')]
else:
	log_level								= logging.NOTSET

logging.basicConfig(
	filename='/tmp/ebscopy-%s.log' % (os.getpid()),
	level=log_level,
	format='%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s'
)

#__version__ = get_distribution('ebscopy').version

#EOF
