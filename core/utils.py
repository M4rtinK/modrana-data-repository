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

URL_GEOFABRIK = 1

def tarDir(path, tarFilename, fakeRoot=None):
  """compress all files in a directory to a (compressed) tar archive"""
  tar = tarfile.TarFile.open(tarFilename, 'w:gz')
  for root, dirs, files in os.walk(path):
    for file in files:
      # use the fake package root if provided
      if fakeRoot:
        inPath = os.path.join(root, file)
        archPath = os.path.relpath(inPath, fakeRoot)
        tar.add(inPath, archPath)
      else:
        tar.add(os.path.join(root, file))
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

def path2components(path, maxDepth = 4096):
  """split a path to a list of components"""
  depth = 0
  components = []
  head, tail = os.path.split(path)
  while depth < maxDepth:
    if tail == "":
      break
    components.append(tail) # we from bottom up
    head, tail = os.path.split(head)
    # limit the depth to some high value, just to be sure
    # not to get stuck in this recursive loop
    depth+=1
  components.reverse() # revert back to the real order
  return components

def url2repoPathFilenameName(url, urlType):
  """extract the repository storage path from the source data URL"""
  wholePath = urlparse.urlparse(url)[2]
  rawRepoPath, filename = os.path.split(wholePath)
  name = filename.split('.')[0]
  # remove the latest suffix
  # introduced by Geofabrik
  name.replace("-latest", "")
  # TODO: something more flexible
  # for generic links
  geofabrikPrefix = "http://download.geofabrik.de/openstreetmap/"
  if url.startswith(geofabrikPrefix):
    # we are currently using the Geofabrik URLs with the openstreetmap prefix
    # -> we drop the openstreetmap prefix, leave the continent/country/city/etc suffix
    # normalize the path to get rid of doubled separators, etc.
    rawRepoPath = os.path.normpath(rawRepoPath)
    # split it to a list of components
    components = path2components(rawRepoPath)
    # ignore leading path separator
    if components[0] in (os.pathsep, os.altsep):
      cutIndex = 2
    else:
      cutIndex = 1
    components = components[cutIndex:]
    if components:
      repoSubPath = os.path.join(*components)
    else:
      repoSubPath = ""
#  if urlType == URL_GEOFABRIK:
#    # we are currently using the Geofabrik URLs with the openstreetmap prefix
#    # -> we drop the openstreetmap prefix, leave the continent/country/city/etc suffix
#    # normalize the path to get rid of doubled separators, etc.
#    rawRepoPath = os.path.normpath(rawRepoPath)
#    # split it to a list of components
#    components = path2components(rawRepoPath)
#    # ignore leading path separator
#    if components[0] in (os.pathsep, os.altsep):
#      cutIndex = 2
#    else:
#      cutIndex = 1
#    repoSubPath = os.path.join(*components[cutIndex:])
  else:
    repoSubPath = rawRepoPath
  # add the package name to the repoSub path
  # so that all the mode packages, checksum files, etc.
  # share a folder
  repoSubPath = os.path.join(repoSubPath, name)
  return repoSubPath, filename, name

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

# from:
# http://www.5dollarwhitebox.org/drupal/node/84
def bytes2PrettyUnitString(bytes):
  bytes = float(bytes)
  if bytes >= 1099511627776:
    terabytes = bytes / 1099511627776
    size = '%.2fTB' % terabytes
  elif bytes >= 1073741824:
    gigabytes = bytes / 1073741824
    size = '%.2fGB' % gigabytes
  elif bytes >= 1048576:
    megabytes = bytes / 1048576
    size = '%.2fMB' % megabytes
  elif bytes >= 1024:
    kilobytes = bytes / 1024
    size = '%.2fKB' % kilobytes
  else:
    size = '%.2fb' % bytes
  return size

def countCSVLines(path, minColumns=1):
  """count all eligible lines in the given CSV file
  NOTE: this just iterates over the file so it should handle really
  large CSV files"""
  f = open(path, "r")
  reader = csv.reader(f)
  lineCount = 0
  for row in reader:
    if len(row) >= minColumns:
      lineCount+=1
  f.close()
  return lineCount

def sortUrlsBySize(urls):
  """sort URLs by their size,
  return a list of (size, url) tuples and the complete size in bytes
  * if opening URL fails, skip it in the result
  * if size is unknown (no 'content-length' in header), store a (None, url) tuple
  to the unknownSizeUrls list
  * the sortedUrls list is extended with the unknownSizeUrls before it is returned
  """
  sortedUrls = []
  unknownSizeUrls = []
  totalSize = 0
  for url in urls:
    try:
      response = urllib2.urlopen(url)
      byteSize = response.info().get('content-length', None)
      if byteSize is None:
        unknownSizeUrls.append((None, url))
      else:
        byteSize = int(byteSize)
        # byte size is returned as a string from the header
        sortedUrls.append((byteSize, url))
        totalSize+=byteSize
    except Exception, e:
      print('size estimation failed for url:')
      print(url)
      print(e)
      traceback.print_exc(file=sys.stdout)
  # sort the list
  sortedUrls.sort()
  print('%d urls sorted by size' % len(sortedUrls))
  print('%d with unknown size' % len(unknownSizeUrls))
  print('%d failed urls' % (len(urls) - len(sortedUrls) + len(unknownSizeUrls)))
  sortedUrls.extend(unknownSizeUrls)
  return sortedUrls, totalSize
