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

import os
import tarfile
import zipfile
import datetime

def tarDir(path, tarFilename, fakeRoot=None):
  """compress all files in a directory to a (compressed) tar archive"""
  tar = tarfile.TarFileCompat(tarFilename, 'w', tarfile.TAR_GZIPPED)
  for root, dirs, files in os.walk(path):
    for file in files:
      # use the fake package root if provided
      if fakeRoot:
        inPath = os.path.join(root, file)
        archPath = os.path.relpath(inPath, fakeRoot)
        tar.write(inPath, archPath)
      else:
        tar.write(os.path.join(root, file))
  tar.close()

def zipDir(path, zipFilename, fakeRoot=None):
  """compress all files in a directory to a zip archive"""
  zip = zipfile.ZipFile(zipFilename, 'w', zipfile.ZIP_DEFLATED)
  for root, dirs, files in os.walk(path):
    for file in files:
      if fakeRoot is not None:
        inPath = os.path.join(root, file)
        archPath = os.path.relpath(inPath, fakeRoot)
        zip.write(inPath, archPath)
      else:
        zip.write(os.path.join(root, file))
  zip.close()

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


# based on http://stackoverflow.com/a/1551394
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
      return str( second_diff / 60 ) + " minutes"
    if second_diff < 86400:
      return str( second_diff / 3600 ) + " hours"
  if day_diff < 7:
    return str(day_diff) + " days"
  if day_diff < 31:
    return str(day_diff/7) + " weeks"
  if day_diff < 365:
    return str(day_diff/30) + " months"
  return str(day_diff/365) + " years"
