#!/bin/bash

# refresh metadata and update packages
sudo dnf -y check-update
sudo dnf -y upgrade --exclude='kernel*'

# save packages that would require a restart so I can know when to restart
NEED_RESTART=$(checkrestart 2>/dev/null)
if [ -n "$NEED_RESTART" ]; then
    echo "$(date): Packages needing restart:" >> ~/update_restart_list.txt
    echo "$NEED_RESTART" >> ~/update_restart_list.txt
fi
