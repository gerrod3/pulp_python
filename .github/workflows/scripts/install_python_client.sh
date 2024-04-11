#!/bin/bash

# WARNING: DO NOT EDIT!
#
# This file was generated by plugin_template, and is managed by it. Please use
# './plugin-template --github pulp_python' to update this file.
#
# For more info visit https://github.com/pulp/plugin_template

set -mveuo pipefail

# make sure this script runs at the repo root
cd "$(dirname "$(realpath -e "$0")")"/../../..

source .github/workflows/scripts/utils.sh

PULP_URL="${PULP_URL:-https://pulp}"
export PULP_URL
PULP_API_ROOT="${PULP_API_ROOT:-/pulp/}"
export PULP_API_ROOT

REPORTED_STATUS="$(pulp status)"
REPORTED_VERSION="$(echo "$REPORTED_STATUS" | jq --arg plugin "python" -r '.versions[] | select(.component == $plugin) | .version')"
VERSION="$(echo "$REPORTED_VERSION" | python -c 'from packaging.version import Version; print(Version(input()))')"

pushd ../pulp-openapi-generator
rm -rf pulp_python-client

if pulp debug has-plugin --name "core" --specifier ">=3.44.0.dev"
then
  curl --fail-with-body -k -o api.json "${PULP_URL}${PULP_API_ROOT}api/v3/docs/api.json?bindings&component=python"
  USE_LOCAL_API_JSON=1 ./generate.sh pulp_python python "$VERSION"
else
  ./generate.sh pulp_python python "$VERSION"
fi

pushd pulp_python-client
python setup.py sdist bdist_wheel --python-tag py3

twine check "dist/pulp_python_client-$VERSION-py3-none-any.whl"
twine check "dist/pulp_python-client-$VERSION.tar.gz"

cmd_prefix pip3 install "/root/pulp-openapi-generator/pulp_python-client/dist/pulp_python_client-${VERSION}-py3-none-any.whl"
tar cvf ../../pulp_python/python-python-client.tar ./dist

find ./docs/* -exec sed -i 's/Back to README/Back to HOME/g' {} \;
find ./docs/* -exec sed -i 's/README//g' {} \;
cp README.md docs/index.md
sed -i 's/docs\///g' docs/index.md
find ./docs/* -exec sed -i 's/\.md//g' {} \;

cat >> mkdocs.yml << DOCSYAML
---
site_name: PulpPython Client
site_description: Python bindings
site_author: Pulp Team
site_url: https://docs.pulpproject.org/pulp_python_client/
repo_name: pulp/pulp_python
repo_url: https://github.com/pulp/pulp_python
theme: readthedocs
DOCSYAML

# Building the bindings docs
mkdocs build

# Pack the built site.
tar cvf ../../pulp_python/python-python-client-docs.tar ./site
popd
popd
