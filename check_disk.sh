#!/bin/bash

# show warning if disk usage is over 80% so I can clean stuff out

THRESHOLD=80

USAGE=$(df -h | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$USAGE" -ge "$THRESHOLD" ]; then
    echo "WARNING: usage is at $USAGE%" | mail -s "Disk Usage Alert"
fi
