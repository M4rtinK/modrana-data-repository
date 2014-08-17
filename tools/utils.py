# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana data repository utility functions
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------
import csv

import os
import tarfile
import traceback
import urllib2
import urlparse
import zipfile
import datetime

# URL types
import sys

def createFolderPath(newPath):
    """Create a path for a directory and all needed parent folders
    -> parent directories will be created
    -> if directory already exists, then do nothing
    -> if there is another filesystem object (like a file)
    with the same name exists, return False"""
    if not newPath:
        print("cannot create folder, wrong path: ", newPath)
        return False
    if os.path.isdir(newPath):
        return True
    elif os.path.isfile(newPath):
        print("cannot create directory, file already exists: '%s'" % newPath)
        return False
    else:
    #    print("creating path: %s" % newPath)
        head, tail = os.path.split(newPath)
        if head and not os.path.isdir(head):
            createFolderPath(head) # NOTE: recursion
        if tail:
            os.mkdir(newPath)
        return True

def prettyTimeDiff(dtSeconds):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    diff = datetime.timedelta(seconds=dtSeconds)
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 60:
            return str(second_diff) + " seconds"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours"
    if day_diff < 7:
        return str(day_diff) + " days"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks"
    if day_diff < 365:
        return str(day_diff / 30) + " months"
    return str(day_diff / 365) + " years"

# from:
# http://www.5dollarwhitebox.org/drupal/node/84
def bytes2PrettyUnitString(input_bytes):
    input_bytes = float(input_bytes)
    if input_bytes >= 1099511627776:
        terabytes = input_bytes / 1099511627776
        size = '%.2fTB' % terabytes
    elif input_bytes >= 1073741824:
        gigabytes = input_bytes / 1073741824
        size = '%.2fGB' % gigabytes
    elif input_bytes >= 1048576:
        megabytes = input_bytes / 1048576
        size = '%.2fMB' % megabytes
    elif input_bytes >= 1024:
        kilobytes = input_bytes / 1024
        size = '%.2fKB' % kilobytes
    else:
        size = '%.2fb' % input_bytes
    return size

def hash_file(file_path):
    with open(file_path, "rb") as f:
        hasher = hashlib.md5()
        block_size = 65536
        buf = f.read(block_size)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(block_size)
        return hasher.hexdigest()