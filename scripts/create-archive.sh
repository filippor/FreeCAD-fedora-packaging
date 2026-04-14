#!/usr/bin/env sh
rm -f freecad-sources.tar.gz
git submodule update --init
/usr/bin/python3 package/scripts/write_version_info.py freecad_version.txt
bash -c 'git ls-files --recurse-submodules | tar  -caf freecad-sources.tar.gz -T-'
echo -n 'freecad-sources.tar.gz'
