#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Simone Caronni <negativo17@gmail.com>
# Licensed under the GNU General Public License Version or later

import json
import re
import os
import shutil
import subprocess
import sys
import tarfile
from urllib.request import Request, urlopen

def main():
    repo_url = 'http://api.snapcraft.io/v2/snaps/info/spotify'

    request = Request(repo_url)
    request.add_header('Snap-Device-Series', '16')
    response = urlopen(request).read()
    repo_url_raw = json.loads(response)

#    print(repo_url_raw['channel-map'][2]['version'])

    for channel_map in repo_url_raw['channel-map']:
        if 'edge' in channel_map['channel']['name']:
            version = channel_map['version']
            snap_url = channel_map['download']['url']

    with open('spotify-client.spec', 'r') as file:
        for line in file:
            if re.search('^Version:.*' + version, line, re.I):
                print("SPEC file already contains the latest version: " + version + ".")
                sys.exit(0)

    print("New version available: " + version + " (" + snap_url + ")")

    print("Updating SPEC file...", end = " ")
    rpmdev_bumpspec_comment = ("Update to version " + version + ".")
    subprocess.run(["rpmdev-bumpspec", "-D", "-c", rpmdev_bumpspec_comment, "-n", version, "spotify-client.spec" ])
    print("done.")

    tarball = ("spotify-" + version)
    
    print("Downloading snap file " + tarball + ".snap" + "...", end=" ", flush=True)
    request = Request(snap_url)
    response = urlopen(request).read()
    open(tarball + ".snap", 'wb').write(response)
    print("done.")

    print("Unpacking " + tarball + ".snap" + "...", end=" ", flush=True)
    subprocess.run(["unsquashfs", "-q", "-n", "-f", "-d", "temp", tarball + ".snap"])
    shutil.move("temp/usr/share/spotify", tarball)
    shutil.rmtree(tarball + "/apt-keys")
    shutil.rmtree("temp")
    os.remove(tarball + ".snap")
    print("done.")

    print("Creating tarball " + tarball + ".tar.xz...", end=" ", flush=True)
    tar = tarfile.open(tarball + ".tar.xz", "w:xz")
    tar.add(tarball)
    tar.close()
    shutil.rmtree(tarball)
    print("done.")

if __name__ == "__main__":
    main()
