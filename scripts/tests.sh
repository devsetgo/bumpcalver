#!/bin/bash
set -e
set -x

#run pre-commit
pre-commit run -a
# bash scripts/test.sh --cov-report=html ${@}
pytest

# TODO: Make Pytest run in parallel
# pytest -n auto

# python3 -m pytest
# python3 -m pytest -v -s
# modify path for
sed -i "s/<source>\/workspace\/devsetgo_lib<\/source>/<source>\/github\/workspace<\/source>/g" /workspaces/devsetgo_lib/coverage.xml
# create coverage-badge
coverage-badge -o coverage.svg -f
