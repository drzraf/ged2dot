#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

#
# Baseline: Windows 2019
#

choco install graphviz
if (-not $?) { throw "error $?" }
# Register plugins.
dot -c
if (-not $?) { throw "error $?" }
choco install wixtoolset
if (-not $?) { throw "error $?" }

cd tools
git clone https://github.com/jpakkane/msicreator
if (-not $?) { throw "error $?" }
cd msicreator
# Allow to add extra attributes to MajorUpgrade node. (#7), 2018-09-08.
git checkout 57c0d083ee8ce6d5c9b417d88aa80a1c8d3d6419
if (-not $?) { throw "error $?" }
cd ..
cd ..

# Allow both 'graphviz' and 'Graphviz <version>'.
$GVPATH = Resolve-Path "C:/Program Files/Graphviz*" | Select -ExpandProperty Path
pip install --global-option=build_ext --global-option="-I${GVPATH}/include" --global-option="-L${GVPATH}/lib/" pygraphviz==1.6
if (-not $?) { throw "error $?" }
python -m pip install -r requirements.txt
if (-not $?) { throw "error $?" }

python tools\pack.py
if (-not $?) { throw "error $?" }

# vim:set shiftwidth=4 softtabstop=4 expandtab:
