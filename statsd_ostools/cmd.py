import logging
import optparse
import os
import socket
import sys
import time
from setproctitle import setproctitle
from statsd.client import StatsClient
from statsd_ostools import worker

log = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: %(message)s')

def main():
    parser = optparse.OptionParser()
    parser.add_option('-H', '--host',
        dest='host', metavar='HOST', default='localhost',
        help='statsd hostname/ip (default: localhost)',
    )
    parser.add_option('-p', '--port',
        dest='port', metavar='PORT', type='int', default=8125,
        help='statsd port (default: 8125)',
    )
    parser.add_option('-P', '--prefix',
        dest='prefix', metavar='PREFIX', default='stats',
        help='statsd prefix (default: stats)',
    )
    parser.add_option('-i', '--interval',
        dest='interval', metavar='INT', type='int', default=10,
        help='interval to pass to stat commands (default: 10)',
    )
    parser.add_option('-d', '--debug',
        dest='debug', action='store_true', default=False,
        help='turn on debugging',
    )
    (opts, args) = parser.parse_args()

    if opts.debug:
        rootlogger = logging.getLogger()
        rootlogger.setLevel(logging.DEBUG)
        del rootlogger

    statsd = StatsClient(opts.host, opts.port, opts.prefix)

    os.environ['LC_ALL'] = 'C' # standardize output format (datetime, ...)
    setproctitle('statsd-ostools: master')
    try:
        kids = []
        for workerklass in worker.workers:
            pid = os.fork()
            kids.append(pid)
            if pid != 0:
                sys.exit(workerklass(statsd, opts.interval).run())

        while True:
            log.debug('master: sleeping...')
            time.sleep(opts.interval)
    except KeyboardInterrupt:
        pass

    sys.exit(0)

if __name__ == '__main__':
    main()