# Checks if there has been a new version change, and builds the plugin for release if there has.
git fetch
git checkout HEAD~
LAST_VER=$(python setup.py -V)
python setup.py -V
git checkout -
LATEST_VER=$(python setup.py -V)
python setup.py -V
if [[ "$LATEST_VER" > "$LAST_VER" ]];then
  echo "Version bumped from $LAST_VER to $LATEST_VER. Building"
  pip install build
  python -m build
else
  echo "Version not bumped. Not building."
fi