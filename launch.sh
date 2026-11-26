#!/bin/sh
cd /home/voidnode/Projects/pixel-pet || exit 1
export QT_QPA_PLATFORM=xcb
exec /usr/bin/python /home/voidnode/Projects/pixel-pet/pet.py "$@"
