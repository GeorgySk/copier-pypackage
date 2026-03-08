#!/bin/bash
set -eux

uid=$(stat -c '%u' "$(pwd)")
gid=$(stat -c '%g' "$(pwd)")

# this was necessary for Windows;
# unclear if this might cause problems on other OS
if [ "$uid" -eq 0 ] && [ "$gid" -eq 0 ]; then
    exit 0
fi

current_user=$(whoami)

if [ "$gid" -ne 1000 ]; then
    sudo groupadd -g "$gid" hostgroup
    if [ "$uid" -ne 1000 ]; then
        sudo usermod -u "$uid" -g hostgroup "$current_user"
    else
        sudo usermod -g hostgroup "$current_user"
    fi
elif [ "$uid" -ne 1000 ]; then
    sudo usermod -u "$uid" "$current_user"
fi
