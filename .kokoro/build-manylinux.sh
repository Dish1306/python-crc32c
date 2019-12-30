#!/bin/bash

# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Need enchant for spell check
sudo apt-get update
sudo apt-get -y install dictionaries-common aspell aspell-en \
	                hunspell-en-us libenchant1c2a enchant

set -eo pipefail

# Disable buffering, so that the logs stream through.
export PYTHONUNBUFFERED=1

# Debug: show build environment
env | grep KOKORO

cd github/python-crc32c

# Before running nox and such, build the extension.
./scripts/manylinux/build.sh
./scripts/manylinux/check.sh


# # Install nox
# python3 -m pip install --upgrade --quiet nox --user
# python3 -m nox --version

# python3 -m nox check
