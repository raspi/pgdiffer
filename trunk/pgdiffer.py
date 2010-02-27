#!/bin/env python
# -*- coding: utf8 -*-
# PostgreSQL database differ
# $Id$

import os
import sys
import traceback
import subprocess

from ConfigParser import ConfigParser
from optparse import OptionParser, Option, OptionGroup

__VERSION__ = "0.0.1"
__AUTHOR__ = u"Pekka Järvinen"
__YEAR__ = 2010
__HOMEPAGE__ = u"http://code.google.com/p/pgdiffer/"

def createIniDict(config, section):
    ret = {}
    items = config.items(section)

    if len(items):
        for i in items:
            (key, val) = i
            ret[key] = val

    return ret

def run(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    return p

# Run pg_dump command
def pgdump(config):
    cmd = [
        'pg_dump',
        '-Fc',
        '--no-acl',
        '--no-owner',
        '-U', config['user'],
        '-h', config['host'],
        config['database']
    ]

    try:
        os.putenv("PGPASSWORD", config['password'])
        p = run(cmd)

        if p.returncode == 0:
            f = open(config['dump'], 'wb')
            f.write(p.stdout.read())
            f.close()
            return True
        else:
            print p.stderr.readlines()
            print p.stdin.readlines()
            print p.stdout.readlines()

    except Exception:
        pass
    
    return False

# Run pg_restore command
def pgrestore(config):
    cmd = [
        'pg_restore',
        '--schema-only',
        '--no-owner',
        config['dump']
    ]

    try:
        p = run(cmd)

        if p.returncode == 0:
            f = open(config['sql'], 'wb')
            f.write(p.stdout.read())
            f.close()

            return True
        else:
            print p.stderr.readlines()
            print p.stdin.readlines()
            print p.stdout.readlines()

    except Exception:
        pass

    return False

# Run apgdiff command
def apgdiff(master, dev, diff):
    cmd = [
        'apgdiff',
        '--quote-names',
        master['sql'],
        dev['sql'],
    ]

    try:
        p = run(cmd)

        if p.returncode == 0:
            f = open(diff['filename'], 'wb')

            for i in p.stdout.readlines():
                i = i.rstrip();
                f.write(i + "\n")

            f.close()

            return True
        else:
            print p.stderr.readlines()
            print p.stdin.readlines()
            print p.stdout.readlines()

    except Exception:
        pass

    return False


if __name__ == "__main__":
    banner  = u"PostgreSQL database differ ver. %s" % (__VERSION__)
    banner += u" (c) %s %s" % (__AUTHOR__, __YEAR__)

    examples = []
    examples.append("")

    usage = "\n".join(examples)

    parser = OptionParser(version="%prog " + __VERSION__, usage=usage, description=banner)

    parser.add_option("--config", "-c", action="store", type="string", dest="config", help="Config INI file defaults to config.ini", default="config.ini")
    
    (options, args) = parser.parse_args()

    if options.config != None:
        options.config = os.path.realpath(options.config)
        
        if not os.path.isfile(options.config):
            print "INI file '%s' not found." % options.config
            sys.exit(1)

        config = ConfigParser()
        config.read(options.config)

        master = createIniDict(config, "master")
        dev = createIniDict(config, "dev")
        diff = createIniDict(config, "diff")

        if False == (pgdump(master) and pgdump(dev)):
            print "Error in dumping process."
            sys.exit(1)

        if False == (pgrestore(master) and pgrestore(dev)):
            print "Error in restoring process."
            sys.exit(1)

        os.unlink(master['dump'])
        os.unlink(dev['dump'])

        if False == apgdiff(master, dev, diff):
            print "Error in diffing process."
            sys.exit(1)

        os.unlink(master['sql'])
        os.unlink(dev['sql'])

        sys.exit(0)

sys.exit(1)