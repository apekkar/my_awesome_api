#!/bin/bash

CURRENT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
INFRA_DIR="$(dirname "$CURRENT_PATH")"
PROJECT_ROOT="$(dirname "$INFRA_DIR")"
REQUIREMENTS_PATH="${PROJECT_ROOT}/requirements.txt"

python3.12 -m venv ./layers/create_layer
source ./layers/create_layer/bin/activate
pip3 install -r ${REQUIREMENTS_PATH} --target ./layers/python --platform manylinux2014_x86_64 --only-binary=:all: psycopg2-binary
deactivate
rm -Rf ./layers/create_layer
