#!/bin/sh
cd /Users/danielgnagi/sandboxzurich && PYTHONWARNINGS=ignore .venv/bin/python research/squares2/tools/xing.py "$@" 2>&1 | grep -v "osm source"
