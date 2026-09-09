#!/bin/sh

# Pip-Licenses Demo Example
# ..................................
# Copyright (c) 2024-2026, Mr. Walls
# ..................................
# Licensed under MIT (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# ..........................................
# https://github.com/raimon49/pip-licenses/tree/HEAD/LICENSE
# ..........................................
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../examples/common.sh"

init_demo

run_command "echo 'Auditing the project dependencies'"
pause 0.9

run_command "pip-licenses --summary"
pause 1.8

run_command "echo"
run_command "echo 'Now showing the complete dependency report'"
pause 1.0

run_command "pip-licenses | head -n 14"
pause 2.2

run_command "echo"
run_command "echo 'The report makes dependency licenses visible at a glance.'"
pause 1.8

printf '\r\n'
