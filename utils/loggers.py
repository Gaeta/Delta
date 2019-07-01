import sys, os

from .helpers import time_fmt, get_ext_err, cleanup_dir_name
from datetime import datetime

def cog_error(error, config):
    origin = cleanup_dir_name(error.name, config.directories, "cogs")
    desc = get_ext_err(error, config)

    print(f"[ {time_fmt()} ] >> [ {origin} ] >> [ Error ]: {desc}", file=sys.stderr)

def error(msg, origin, terminate=False):
    print(f"[ {time_fmt()} ] >> [ {origin} ] >> [ Error ]: {msg}", file=sys.stderr)

    if terminate:
        os._exit(2)