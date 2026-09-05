#!/usr/bin/env bash
# Disclaimer of Warranties.
# A. YOU EXPRESSLY ACKNOWLEDGE AND AGREE THAT, TO THE EXTENT PERMITTED BY
#    APPLICABLE LAW, USE OF THIS SHELL SCRIPT AND ANY SERVICES PERFORMED
#    BY OR ACCESSED THROUGH THIS SHELL SCRIPT IS AT YOUR SOLE RISK AND
#    THAT THE ENTIRE RISK AS TO SATISFACTORY QUALITY, PERFORMANCE, ACCURACY AND
#    EFFORT IS WITH YOU.
#
# B. TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THIS SHELL SCRIPT
#    AND SERVICES ARE PROVIDED "AS IS" AND "AS AVAILABLE", WITH ALL FAULTS AND
#    WITHOUT WARRANTY OF ANY KIND, AND THE AUTHOR OF THIS SHELL SCRIPT'S LICENSORS
#    (COLLECTIVELY REFERRED TO AS "THE AUTHOR" FOR THE PURPOSES OF THIS DISCLAIMER)
#    HEREBY DISCLAIM ALL WARRANTIES AND CONDITIONS WITH RESPECT TO THIS SHELL SCRIPT
#    SOFTWARE AND SERVICES, EITHER EXPRESS, IMPLIED OR STATUTORY, INCLUDING, BUT
#    NOT LIMITED TO, THE IMPLIED WARRANTIES AND/OR CONDITIONS OF
#    MERCHANTABILITY, SATISFACTORY QUALITY, FITNESS FOR A PARTICULAR PURPOSE,
#    ACCURACY, QUIET ENJOYMENT, AND NON-INFRINGEMENT OF THIRD PARTY RIGHTS.
#
# C. THE AUTHOR DOES NOT WARRANT AGAINST INTERFERENCE WITH YOUR ENJOYMENT OF THE
#    THE AUTHOR's SOFTWARE AND SERVICES, THAT THE FUNCTIONS CONTAINED IN, OR
#    SERVICES PERFORMED OR PROVIDED BY, THIS SHELL SCRIPT WILL MEET YOUR
#    REQUIREMENTS, THAT THE OPERATION OF THIS SHELL SCRIPT OR SERVICES WILL
#    BE UNINTERRUPTED OR ERROR-FREE, THAT ANY SERVICES WILL CONTINUE TO BE MADE
#    AVAILABLE, THAT THIS SHELL SCRIPT OR SERVICES WILL BE COMPATIBLE OR
#    WORK WITH ANY THIRD PARTY SOFTWARE, APPLICATIONS OR THIRD PARTY SERVICES,
#    OR THAT DEFECTS IN THIS SHELL SCRIPT OR SERVICES WILL BE CORRECTED.
#    INSTALLATION OF THIS THE AUTHOR SOFTWARE MAY AFFECT THE USABILITY OF THIRD
#    PARTY SOFTWARE, APPLICATIONS OR THIRD PARTY SERVICES.
#
# D. YOU FURTHER ACKNOWLEDGE THAT THIS SHELL SCRIPT AND SERVICES ARE NOT
#    INTENDED OR SUITABLE FOR USE IN SITUATIONS OR ENVIRONMENTS WHERE THE FAILURE
#    OR TIME DELAYS OF, OR ERRORS OR INACCURACIES IN, THE CONTENT, DATA OR
#    INFORMATION PROVIDED BY THIS SHELL SCRIPT OR SERVICES COULD LEAD TO
#    DEATH, PERSONAL INJURY, OR SEVERE PHYSICAL OR ENVIRONMENTAL DAMAGE,
#    INCLUDING WITHOUT LIMITATION THE OPERATION OF NUCLEAR FACILITIES, AIRCRAFT
#    NAVIGATION OR COMMUNICATION SYSTEMS, AIR TRAFFIC CONTROL, LIFE SUPPORT OR
#    WEAPONS SYSTEMS.
#
# E. NO ORAL OR WRITTEN INFORMATION OR ADVICE GIVEN BY THE AUTHOR
#    SHALL CREATE A WARRANTY. SHOULD THIS SHELL SCRIPT OR SERVICES PROVE DEFECTIVE,
#    YOU ASSUME THE ENTIRE COST OF ALL NECESSARY SERVICING, REPAIR OR CORRECTION.
#
#    Limitation of Liability.
# F. TO THE EXTENT NOT PROHIBITED BY APPLICABLE LAW, IN NO EVENT SHALL THE AUTHOR
#    BE LIABLE FOR PERSONAL INJURY, OR ANY INCIDENTAL, SPECIAL, INDIRECT OR
#    CONSEQUENTIAL DAMAGES WHATSOEVER, INCLUDING, WITHOUT LIMITATION, DAMAGES
#    FOR LOSS OF PROFITS, CORRUPTION OR LOSS OF DATA, FAILURE TO TRANSMIT OR
#    RECEIVE ANY DATA OR INFORMATION, BUSINESS INTERRUPTION OR ANY OTHER
#    COMMERCIAL DAMAGES OR LOSSES, ARISING OUT OF OR RELATED TO YOUR USE OR
#    INABILITY TO USE THIS SHELL SCRIPT OR SERVICES OR ANY THIRD PARTY
#    SOFTWARE OR APPLICATIONS IN CONJUNCTION WITH THIS SHELL SCRIPT OR
#    SERVICES, HOWEVER CAUSED, REGARDLESS OF THE THEORY OF LIABILITY (CONTRACT,
#    TORT OR OTHERWISE) AND EVEN IF THE AUTHOR HAS BEEN ADVISED OF THE
#    POSSIBILITY OF SUCH DAMAGES. SOME JURISDICTIONS DO NOT ALLOW THE EXCLUSION
#    OR LIMITATION OF LIABILITY FOR PERSONAL INJURY, OR OF INCIDENTAL OR
#    CONSEQUENTIAL DAMAGES, SO THIS LIMITATION MAY NOT APPLY TO YOU. In no event
#    shall THE AUTHOR's total liability to you for all damages (other than as may
#    be required by applicable law in cases involving personal injury) exceed
#    the amount of five dollars ($5.00). The foregoing limitations will apply
#    even if the above stated remedy fails of its essential purpose.
################################################################################
#
# common.sh - Shared utilities for pip-licenses examples
#
# This file provides common functions and utilities used by all example scripts.
# It follows the DIP (Dependency Inversion Principle) by providing abstractions
# for environment setup, error handling, and output validation.
#
# Usage:
#   source "${SCRIPT_DIR}/common.sh"

# Keep output predictable and unbuffered where possible.
export LANG=C
export LC_ALL=C

typing_delay=0.035
prompt='demo$ '

# Color codes for output (used by test harness, not examples)
if [[ -t 1 ]]; then
    readonly COLOR_GREEN="\\x1B\\x5B\\x31\x3B\\x33\\x32\\x6D"
    readonly COLOR_RED="\\x1B\\x5B\\x31\x3B\\x33\\x31\\x6D"
    readonly COLOR_YELLOW="\\x1B\\x5B\\x31\x3B\\x33\\x33\\x6D"
    readonly COLOR_RESET="\\x1B\\x5B\\x30\\x6D"
else
    readonly COLOR_GREEN=''
    readonly COLOR_RED=''
    readonly COLOR_YELLOW=''
    readonly COLOR_RESET=''
fi

# Logging functions
log_info() {
    printf "%s\n" "[INFO] $*" >&2
}

log_error() {
    printf "${COLOR_RED}%s${COLOR_RESET}\n" "[ERROR] $*" >&2
}

log_success() {
    printf "${COLOR_GREEN}%s${COLOR_RESET}\n" "[SUCCESS] $*" >&2
}

log_warn() {
    printf "${COLOR_YELLOW}%s${COLOR_RESET}\n" "[WARN] $*" >&2
}

# Check if pip-licenses is installed
check_pip_licenses() {
    if ! command -v pip-licenses &> /dev/null; then
        log_error "pip-licenses is not installed"
        echo "Install it with: pip install pip-licenses" >&2
        return 1
    fi
    return 0
}

# Get the Python interpreter being used
get_python_interpreter() {
    command -v python3 || command -v python
}

get_python_pip() {
    PYTHON_TOOL=$(get_python_interpreter);
    ${PYTHON_TOOL} -B -m pip $@ ;
}

# Check if required packages are installed
check_required_packages() {
    local required_packages=("Django" "pytz")

    for pkg in "${required_packages[@]}"; do
        if ! get_python_pip list 2>/dev/null | tail -n+3 2>/dev/null | grep -q -Ee "^${pkg} "; then
            log_warn "Package ${pkg} is not installed"
            log_info "Install with: pip install ${pkg}"
            return 1
        #else
            #log_info "Package ${pkg} found"
            #get_python_pip show ${pkg}
        fi
    done
    return 0
}

# Detect if running in a virtual environment
is_venv_active() {
    [[ -n "${VIRTUAL_ENV:-}" ]] && return 0 || return 1
}

# Detect if in system environment (not recommended for examples)
is_system_env() {
    ! is_venv_active
}

# Validate that examples use pinned versions
validate_pinned_versions() {
    local django_version="6.0.6"
    local pytz_version="2026.2"

    if ! pip show django | grep -q "Version: ${django_version}"; then
        log_warn "Django version mismatch (expected: ${django_version})"
        return 1
    fi

    if ! pip show pytz | grep -q "Version: ${pytz_version}"; then
        log_warn "pytz version mismatch (expected: ${pytz_version})"
        return 1
    fi

    return 0
}

pause() {
    if [[ ${PIPL_TTYREC_MODE:-0} -eq 1 ]] ; then
        sleep "$1"
    fi ;
}

# Print a command as if it were being typed.
type_command() {
    command=$1
    remaining=$command

    while [ -n "$remaining" ]; do
        next=${remaining#?}
        character=${remaining%"$next"}

        printf '%s' "$character"
        sleep "$typing_delay"

        remaining=$next
    done ;

    printf '\r\n'
}


# Show the prompt, type a command, then execute it.
# Usage: run_command pip-licenses --format=json
run_command() {
    command=$1
    local exit_code

    # printf '\r%s' "$prompt"
    type_command "$command"
    sh -c "$command" || exit_code=$?
    printf '\n%s' "$prompt"
    return "${exit_code:-0}"
}

# clear the screen for a demo and setup the initial prompt
init_demo() {
    # Clear the terminal using ANSI escape sequences rather than relying on
    # the platform-specific clear command.
    # \033[ - CSI
    # 2J - go to top-left
    # H - clear forward (until end)
    printf '\033[2J\033[H'

    # initial prompt
    printf '\n%s' "$prompt"
}

# Verify command executed successfully
verify_success() {
    if [[ $? -eq 0 ]]; then
        log_success "Command succeeded"
        return 0
    else
        log_error "Command failed"
        return 1
    fi
}

# Export for use in subshells
# take care to avoid shellshock
export -f log_info log_error log_success log_warn
export -f check_pip_licenses check_required_packages
export -f is_venv_active is_system_env
export -f get_python_interpreter
