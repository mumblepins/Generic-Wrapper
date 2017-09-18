from __future__ import print_function

import argparse
import os
import subprocess
import sys
import tempfile
import time
from Queue import Queue
from logging.config import dictConfig
from pprint import pformat
from threading import Thread
from humanfriendly import format_size

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


import logging

PREFIX = "GWX"

OPTIONS = dict(
    DEL="DEL",
    DEL_ALL="DEL_ALL",
    REPLACE_ARG="R_ARG",
    REPLACE_OPT="R_OPT",
    ADD="ADD",
    PROGRAM="PROG"
)

ENV_PREFIX = PREFIX + "_"
ARG_PREFIX = "--" + PREFIX + "_"
OS_ENV = os.environ
LOG_FILE = os.path.join(tempfile.gettempdir(), os.path.basename(sys.argv[0]) + '.log')
LOG_LEVEL = logging.DEBUG

FILE_MODE = 'w'
if os.path.isfile(LOG_FILE) and time.time() - os.path.getmtime(LOG_FILE) < 30:
    with open(LOG_FILE, 'a') as fh:
        fh.writelines(['\n', '\n',
                       '============================================NEW LOG============================================\n'])
    FILE_MODE = 'a'


def process_env(env=OS_ENV, prefix=ENV_PREFIX):
    """
    Parses argument variables into ones intended for the wrapper and other
    Returns:

    """
    our_env = {}
    other_env = {}

    for key, var in env.items():
        if key.startswith(ENV_PREFIX):
            our_env[key] = var
        else:
            other_env[key] = var
    return our_env, other_env


def reader(pipe, queue, name):
    try:
        with pipe:
            for line in pipe:
                queue.put((name, line))
    finally:
        queue.put((name, None))


def watch_ps_iter(ps):
    q = Queue()
    threads = []
    mon_list = []
    if ps.stdout is not None:
        mon_list.append('stdout')
        threads.append(Thread(target=reader, args=[ps.stdout, q, 'stdout']))
    if ps.stderr is not None:
        mon_list.append('stderr')
        threads.append(Thread(target=reader, args=[ps.stderr, q, 'stderr']))
    [t.start() for t in threads]
    while mon_list != []:
        name, line = q.get()
        if line is None:
            mon_list.remove(name)
            continue
        yield name, line


def watch_ps(ps):
    for t, ln in watch_ps_iter(ps):
        if ps.stdout is not None and t == 'stdout':
            print(ln)
        elif ps.stderr is not None and t == 'stderr':
            eprint(ln)


def lstrip_count(string, char):
    count = 0
    while string.startswith(char):
        count += 1
        string = string[len(char):]
    return string, count


logging_config = dict(
    version=1,
    formatters={
        'f': {'format':
                  '%(asctime)s %(name)-12.12s %(levelname)-8.8s %(lineno)-5.5d %(message)s'}
    },
    handlers={
        'fh': {'class': 'logging.FileHandler',
               'formatter': 'f',
               'filename': LOG_FILE,
               'level': logging.DEBUG,
               'mode': FILE_MODE, },
        'sh': {'class': 'logging.StreamHandler',
               'formatter': 'f',
               'level': logging.DEBUG}
    },
    root={
        'handlers': ['fh'],
        'level': LOG_LEVEL,
    }
)

dictConfig(logging_config)

log = logging.getLogger()

our_vars, other_vars = process_env()

log.debug(pformat(sys.argv))

parser = argparse.ArgumentParser()
for value in OPTIONS.values():
    parser.add_argument(ARG_PREFIX
                        + value, action='append')
known_args, unknown_args = parser.parse_known_args()
known_args = vars(known_args)
# pprint(known_args)
our_arg_vars = {}
# for k, v in [a.split('=', 2) for a in known_args[ARG_PREFIX]]:
#     our_vars[k] = v


mod_list = {}
for k, v in OPTIONS.items():
    if k in ['PROGRAM']:
        continue
    mod_list[k] = []
    full_name = ENV_PREFIX + v
    log.debug(full_name)
    if full_name in known_args and known_args[full_name] is not None:
        log.debug(known_args[full_name])
        mod_list[k].extend(known_args[full_name])
    if full_name in our_vars and our_vars[full_name] is not None:
        log.debug(our_vars[full_name])
        mod_list[k].extend(our_vars[full_name].split('|'))

mod_list['REPLACE_ARG'] = {b[0]: b[1] for b in [a.split("=", 2) for a in mod_list['REPLACE_ARG']]}

mod_list['REPLACE_OPT'] = {b[0]: b[1] for b in [a.split("=", 2) for a in mod_list['REPLACE_OPT']]}
log.debug(pformat(mod_list))

prog_arg = ENV_PREFIX + OPTIONS['PROGRAM']
new_arg = []
if prog_arg in known_args and known_args[prog_arg] is not None:
    new_args = [known_args[prog_arg]]
elif prog_arg in our_vars and our_vars[prog_arg] is not None:
    new_args = [our_vars[prog_arg]]
else:
    raise EnvironmentError('Program name not found')

if len(mod_list['ADD']) > 0:
    log.debug(mod_list['ADD'])
    new_args.extend(mod_list['ADD'])

iterarg = iter(unknown_args)
log.debug(unknown_args)
for arg in iterarg:
    if arg.startswith('-') or arg.startswith('--'):
        arg_name, dashes = lstrip_count(arg, '-')
        if arg_name in mod_list['DEL']:
            log.debug("Deleting '%s'", arg_name)
            # delete (ignore)
            continue
        if arg_name in mod_list['DEL_ALL']:
            # delete this and the next one
            n = next(iterarg)
            log.debug("Deleting '%s' with argument '%s'", arg_name, n)
            continue
        if arg_name in mod_list['REPLACE_ARG']:
            new_args.append(arg)
            new_args.append(mod_list['REPLACE_ARG'][arg_name])
            n = next(iterarg)
            log.debug("Replacing option '%s' argument '%s' with '%s'", arg, n, mod_list['REPLACE_ARG'][arg_name])
            continue
        if arg_name in mod_list['REPLACE_OPT']:
            log.debug("Replacing option '%s' with '%s'", arg_name, mod_list['REPLACE_OPT'][arg_name])
            new_args.append(('-' * dashes) + mod_list['REPLACE_OPT'][arg_name])
            continue
    new_args.append(arg)

log.debug(pformat(new_args))

proc = subprocess.Popen(new_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
for t, ln in watch_ps_iter(proc):
    if t == 'stdout':
        sys.stdout.write(ln)
        sys.stdout.flush()
        log.debug("STDOUT: %s", ln.rstrip())
    else:
        sys.stderr.write(ln)
        sys.stderr.flush()
        log.debug("STDERR: %s", ln.rstrip())

sys.exit(proc.poll())
