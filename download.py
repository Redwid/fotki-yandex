#!/usr/bin/env python -*- coding: utf-8 -*-
#source: https://github.com/sumkincpp/yfd/blob/master/readme.md
#easy_install progressbar
#http://stackoverflow.com/questions/3002085/python-to-print-out-status-bar-and-percentage
#To fix UnicodeEncodeError follow this link:
#https://stackoverflow.com/questions/9942594/unicodeencodeerror-ascii-codec-cant-encode-character-u-xa0-in-position-20
#Run in shell: export LC_ALL='en_US.utf8'

import os
import time
import re
import urllib2
#import urllib.request
import json
import argparse
import sys
import locale
import progressbar
import commands

oauth_header = "OAuth {}"
user_url = "http://api-fotki.yandex.ru/api/users/{}/albums/?format=json"
album_url = "http://api-fotki.yandex.ru/api/users/{}/album/{}/photos/?format=json"

CREATED = 1
PUBLISHED = 2

def encodeForPrint(text):
    return text.encode('utf-8')

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def fileExist(filename, bytesize, display_progress):
    if os.path.exists(filename):
        filesize = os.path.getsize(filename) 
        if long(filesize) == long(bytesize):
            #if display_progress == False:
            #    print(u'"{}" already exists. Skipped.'.format(encodeForPrint(filename)))
            return True
        #else:
        #    if display_progress == False:    
        #        #print(u'"{}" has a different size. Expected: {}, original: {}'.format(filename, bytesize, filesize)) 
        #        print(u'"{}" has a different size. Expected: {}, original: {}'.format(encodeForPrint(filename), sizeof_fmt(bytesize), sizeof_fmt(filesize))) 
    return False

# Downlaod file and set the timestamp
# returns: 
#   0 - skipped as file exists
#   1 - downlaoded
#  -1 - error
def download(oauth_token, filename, url, t, display_progress):
    try:
        req = urllib2.Request(url)
        if oauth_token != "":
            req.add_header("Authorization", oauth_header.format(oauth_token))
        response = urllib2.urlopen(req)
        bytesize = response.headers['content-length']
        if fileExist(filename, long(bytesize), display_progress):
            return 0

        f = open(filename, mode="wb")
        f.write(response.read())
        f.close()
        os.utime(filename, (time.time(), t))
        return 1
    except IOError as e:
        print(u'  Error, file: {} cannot be saved, url: {}, e: {}, {}'.format(encodeForPrint(filename), url, e.errno, e.strerror)) 
    return -1     

def getFileName(album_dir, use_title, imageTitle, imageId):
    fileName = "none.jpg"
    if use_title and imageTitle.lower() not in ["", ".jpg"]:
        fileName = os.path.join(album_dir, imageTitle)
        if not imageTitle.lower().endswith(".jpg"):
            fileName += ".jpg"    
    else:        
        fileName = os.path.join(album_dir, re.search("\d+$", imageId).group() + ".jpg")
    return fileName    

def updateProgress(display_progress, bar, progress, total, text):
    if display_progress:
        bar.update(progress*100/total)
    elif text != "":
        print(text)

def grab(user_id, oauth_token, album_id, dest, use_title, imageCount, display_progress):
    url = album_url.format(user_id, album_id)
    
    index = 0
    skippedCount = 0
    downloadedCount = 0
    failedCount = 0
    currentImagesCount = 0
    albumTitle = ""

    bar = progressbar.ProgressBar(maxval = 100, \
        widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])

    if display_progress:
        bar.start()

    while True:
        req = urllib2.Request(url)
        if oauth_token != "":
            req.add_header("Authorization", oauth_header.format(oauth_token))
        album = json.loads(urllib2.urlopen(req).read().decode("utf-8"))
        if not "entries" in album:
            return

        album_dir = os.path.join(dest, album["title"])
        if not os.path.isdir(album_dir):
            os.makedirs(album_dir)

        albumTitle = album["title"]
        currentImagesCount = currentImagesCount + len(album["entries"])
        maxCurrentImagesCount = max(imageCount, currentImagesCount)

        #if display_progress == False:
        #    print(u'Downloading album "{}" (id: {}), from {} to {}'.format(encodeForPrint(albumTitle), album_id, index, currentImagesCount))
        for image in album["entries"]:
            index = index + 1
            
            if "created" in image:
                t = time.mktime(time.strptime(image["created"], "%Y-%m-%dT%H:%M:%SZ"))
            elif "published" in image:
                t = time.mktime(time.strptime(image["published"], "%Y-%m-%dT%H:%M:%SZ"))
            else:
                t = time.time()

            fileName = getFileName(album_dir, use_title, image["title"], image["id"])    

            if fileExist(fileName, image["img"]["orig"]["bytesize"], display_progress):
                skippedCount = skippedCount + 1
                updateProgress(display_progress, bar, index, maxCurrentImagesCount, "")
            else: 
                value = download(oauth_token, fileName, image["img"]["orig"]["href"], t, display_progress)    
                if value == 0:
                    skippedCount = skippedCount + 1
                    updateProgress(display_progress, bar, index, maxCurrentImagesCount, "")
                elif value == 1:
                    downloadedCount = downloadedCount + 1
                    updateProgress(display_progress, bar, index, maxCurrentImagesCount, u'  Saved "{}", time: {} {}/{}'.format(encodeForPrint(fileName), time.strftime("%b %d %Y %H:%M:%S", time.gmtime(t)), index, currentImagesCount))
                elif value == -1:
                    failedCount = failedCount + 1

        links = album["links"]
        if"next" not in links:
            break
        url = links["next"]                 
        if not url: 
            break
    if display_progress:        
        bar.finish()
    print(u'  Files: {} (skipped: {}, downloaded: {}, failed: {})'.format(currentImagesCount, skippedCount, downloadedCount, failedCount))


if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    parser = argparse.ArgumentParser(description="Downloads albums from Yandex.Fotki. Skips files that already exist.")
    parser.add_argument("user")
    parser.add_argument("-a", "--albums", nargs="*", metavar="ID", help="list of album ids to proceed (download all if empty, prompt for every album if the argument is omitted)")
    parser.add_argument("-d", "--dest", default="", metavar="DIR", help="output directory")
    parser.add_argument("-t", "--use-title", action="store_true", help="use title as file name (if possible)")
    parser.add_argument("-p", "--display-progress", action="store_true", help="use progress for download and disable all debug output")
    parser.add_argument("-o", "--oauth-token", help="use to provide OAuth token")
    args = parser.parse_args()

    url = user_url.format(args.user)
    user = json.loads(urllib2.urlopen(url).read().decode("utf-8"))
    if "entries" in user:
        for album in user["entries"]:
            imageCount = album["imageCount"]
            if imageCount == 0:
                continue
            album_id = re.search("\d+$", album["id"]).group()

            album_title = album["title"]#.encode('cp1251').decode('utf8')
            print(u'Download album {} (id: {})? '.format(encodeForPrint(album_title), album_id))
            
            one = args.albums is None and raw_input("") in ["y", "Y"];
            two = args.albums is not None and (args.albums == [] or album_id in args.albums);
            
            if (one or two):
                grab(args.user, args.oauth_token, album_id, args.dest, args.use_title, imageCount, args.display_progress)
    
    dir_size = commands.getoutput('du -sh {}'.format(args.dest)).split()[0]
    print(u'Destination folder size: {}'.format(dir_size))
