#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python sandip_university/manage.py collectstatic --no-input

python sandip_university/manage.py migrate
