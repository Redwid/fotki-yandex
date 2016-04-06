Yandex.Fotki Downloaders
========================

This is a forked version of the https://github.com/sumkincpp/yfd python script


Python download.py
------------------

Allows to download all albums from Yandex.Fotki including private albums and albums that have more than 100 photos inside.

Script checks if the file exists in destination folder and the size is the same.
There are two checks on the file size: the first one is from yandex meta data (sometimes it's reported incorrect size) and the second check - is 'content-length' value from server responce.

Tested and worked on python 2.7.3 @ Debian wheezy

Dependency: progressbar
To install run: sudo easy_install progressbar

### Usage

For help

    python download.py -h

Downloading albums from user hello (interactive)

    python download.py hello

Downloading album by id from user hello

    python download.py hello -a 4632

Downloading all albums (including private) for the user hello (designed to use from cron)

    python download.py hello -d /media/photos -o OAUTH_TOKEN -a -t

Downloading all albums (including private) for the user hello and display progress bar:

    python download.py hello -d /media/photos -o OAUTH_TOKEN -a -t -p




