#!/bin/bash

PATH_VENV="venv/Scripts/activate"
PATH_SRC="src"
PATH_DST="src_minified"


if [[ -f $PATH_VENV ]]; then
    . $PATH_VENV
else
    echo "venv not available: $PATH_VENV"
fi

echo "Pyminify $(pyminify --version)"

# copy src files
echo "Copying files"
cp -r --parents $PATH_SRC $PATH_DST

# minify them
minify () {
    shopt -s nullglob dotglob
    
    for pathname in "$1"/*; do
        if [ -d "$pathname" ]; then
            minify "$pathname"
        else
            echo "$pathname"
            pyminify $pathname >> "$pathname.min"
            rm $pathname
            mv "$pathname.min" $pathname
        fi
    done
}

minify "$PATH_DST/$PATH_SRC"

# move the files up from the parent dir in the target dir
mv "$PATH_DST/$PATH_SRC"/* "$PATH_DST"
rmdir "$PATH_DST/$PATH_SRC"