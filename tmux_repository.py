#!/usr/bin/python
# a wrapper that runs the repository update inside a tmux session
# * the summary log goes to the main tab
# * the other tabs have the individual pool logs

import os
import time
import sys
import subprocess

log_folder = "logs/repo_update_logs_%s" % time.strftime("%Y.%m.%d-%H:%M:%S")
print("log folder: %s" % log_folder)

#cmd = "tmux -u -f /usr/share/anaconda/tmux.conf start"

os.environ['REPO_ARGV'] = " ".join(sys.argv[1:])
os.environ['LOGS'] = log_folder
print("starting tmux wrapper")
subprocess.check_call(['tmux', '-u', '-f', 'core/data/tmux.conf', 'start'],
                      env=os.environ)
subprocess.check_call(['tmux', 'attach'],
                      env=os.environ)
print("tmux wrapping done")
