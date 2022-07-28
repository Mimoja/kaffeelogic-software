#!/bin/bash
~/.local/bin/pyinstaller 'Kaffelogic Studio.spec'
sh ubuntu-package.sh
python linux-build.py
