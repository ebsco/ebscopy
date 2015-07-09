# ebscopy __init__

import os
import logging 
from ebscopy import *
from pkg_resources import get_distribution, DistributionNotFound

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

try: 
	_dist									= get_distribution("ebscopy")
	dist_loc								= os.path.normcase(_dist.location)
	here									= os.path_normcase(__file__)
	if not here.startswith(os.path.join(dist_loc, "ebscopy")):
		raise DistributionNotFound
except DistributionNotFound:
	__version__ 							= 0
else:
	__version__								= _dist.version

logging.info("Version is %s" % __version__)


#EOF
