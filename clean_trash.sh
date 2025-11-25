#!/bin/bash

TRASH="$HOME/.local/share/Trash"

# remove all files older than 30 days
find "$TRASH" -type f -mtime +30 -exec rm -f {} \;

# remove all files older than 7 days if they're over 1GB
find "$TRASH" -type f -size +1G -mtime +7 -exec rm -f {} \;
