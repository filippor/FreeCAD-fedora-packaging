#!/usr/bin/env sh
git submodule update --init
bash -c 'git ls-files --recurse-submodules | tar  -caf freecad-sources.tar.gz -T-'
echo -n 'freecad-sources.tar.gz'
