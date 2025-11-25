#!/bin/bash

# extract all magnet links and torrent names from qbittorrent flatpak configs

BT_BACKUP="$HOME/.var/app/org.qbittorrent.qBittorrent/data/qBittorrent/BT_backup"

if [ ! -d "$BT_BACKUP" ]; then
    echo "BT backup folder not found at $BT_BACKUP"
    exit 1
fi

for TORRENT in "$BT_BACKUP"/*.torrent; do
    TORRENT_NAME=$(transmission-show "$TORRENT" | awk -F': ' '/Name/ {print $2}')
    MAGNET=$(transmission-show -m "$TORRENT")
    echo "$TORRENT_NAME | $MAGNET"
done
