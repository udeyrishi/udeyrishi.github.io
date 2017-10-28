#!/usr/bin/env python2

import argparse
from subprocess import call, check_output, CalledProcessError, Popen
import re
import sys
import logging
from functools import total_ordering
import signal

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def main(args):
    min_ruby_version = Version(major=2, minor=1, rev=0)

    ruby_version = get_ruby_version()
    if ruby_version is None:
        return -1

    logger.info('Ruby version {0} found...'.format(ruby_version))
    if ruby_version < min_ruby_version:
        logger.error('Ruby version {0}+ needed'.format(min_ruby_version))
        return -1

    if args.refetch:
        logger.info('Installing or updating bundler...')
        code = call(['gem', 'install', 'bundler'])
        if code != 0:
            logger.error('Bundler installation failed')
            return -1

        logger.info('Resolving dependencies...')
        code = call(['bundle', 'install'])
        if code != 0:
            logger.error('Dependency installation failed')
            return -1
    elif not is_bundler_installed():
        logger.error('Bundler not installed. Please use the -r option')
        return -1

    logger.info('Starting server...')
    server = Popen(['bundle', 'exec', 'jekyll', 'serve', '--force_polling'], stdout=sys.stdout, stderr=sys.stderr)
    pid = server.pid
    try:
        server.communicate()
    except KeyboardInterrupt:
        server.send_signal(signal.SIGINT)
    return 0


def is_bundler_installed():
    try:
        check_output(['which', 'bundle'])
        return True
    except CalledProcessError:
        return False


def get_ruby_version():
    try:
        ruby_version = check_output(['ruby', '--version'])
    except CalledProcessError:
        logger.error('Ruby not installed')
        return None

    match_obj = re.match(r'^ruby ([0-9]+).([0-9]+).([0-9]+).*$', ruby_version)
    if not match_obj:
        logger.error('Unknown ruby version: ' + ruby_version)
        return None

    return Version(major=int(match_obj.group(1)), minor=int(match_obj.group(2)), rev=int(match_obj.group(3)))


@total_ordering
class Version:
    def __init__(self, major, minor, rev):
        self.major = major
        self.minor = minor
        self.rev = rev

    def __eq__(self, other):
        return (self.major, self.minor, self.rev) == (other.major, other.minor, other.rev)

    def __lt__(self, other):
        return (self.major, self.minor, self.rev) < (other.major, other.minor, other.rev)

    def __str__(self):
        return 'v{0}.{1}.{2}'.format(self.major, self.minor, self.rev)

    def __repr__(self):
        return self.__str()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='build and start the Jekyll site')
    parser.add_argument('-r', '--refetch', help='refetch dependencies before running', action='store_true')
    sys.exit(main(parser.parse_args()))
