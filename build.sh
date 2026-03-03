#!/bin/bash

source $(pwd)/.venv/bin/activate
source $(pwd)/install/setup.zsh
colcon build --parallel-workers $(nproc) --symlink-install
