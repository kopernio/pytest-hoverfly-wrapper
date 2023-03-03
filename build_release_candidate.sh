#!/usr/bin/env bash

# Checks if there has been a new version change, and builds the plugin for release if there has.
pip install yolk3k
LATEST_DEPLOYED_VER=$(yolk -V pytest-hoverfly-wrapper | grep -oE '[0-9.]+')
THIS_VER=$(python setup.py -V)
if [[ "$THIS_VER" > "$LATEST_DEPLOYED_VER" ]];then
  echo "Version bumped from $LATEST_DEPLOYED_VER to $THIS_VER. Building"
  pip install build
  python -m build
else
  echo "Version not bumped. Not building."
fi