#!/bin/sh
mkdir -p "$HOME/.config/systemd/user"
cp "$(dirname "$0")"/systemd/library-catalogue.service "$(dirname "$0")"/systemd/library-catalogue.timer "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now library-catalogue.timer
systemctl --user list-timers library-catalogue.timer --no-pager
