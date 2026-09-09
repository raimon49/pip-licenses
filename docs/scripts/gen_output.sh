#! /bin/bash
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
# Generate examples for inclusion in documentation by running the example
# automation scripts in a repeatable venv (via make setup-examples).
#

set -euo pipefail

# Inputs:
# Example's ID: e.g., NN=[00-99]{2} (zero-lead 0-99)
EXAMPLE_NUM="${1:-01}"

# Dir numbers are more limited
case "${EXAMPLE_NUM%?}" in
    0|x|X)
        EXAMPLE_DIR_NUM="0${EXAMPLE_NUM#?}"
    ;;
    1|2|3|4|5|6|7|8|9)
        EXAMPLE_DIR_NUM="${EXAMPLE_NUM%?}*"
    ;;
    *)
        printf "Error: %s\n" "Invalid Id: $EXAMPLE_NUM" ;
    ;;
esac

DIR_STUB="${2:-basic}"

# Example's Directory: any NN-*
EXAMPLE_DIR_HINT="${EXAMPLE_DIR_NUM}-${DIR_STUB:-}"

# Example's name in the form: NN-*-*
#                             ^^ ^ ^
#                   Example's ID | |
#               Example's Prefix + |
#           Example's Unique Desc. +
# E.g., 01-basic-usage (in 01-basic)
EXAMPLE_NAME_HINT="${EXAMPLE_NUM:-}-${DIR_STUB:-}-${3:-*}"

# Rest of variables
#
PREFIX_STUB_HINT=$(dirname "${0}")/../examples/"${EXAMPLE_DIR_HINT:-}" ;
{ test -d ${PREFIX_STUB_HINT:-} ;} || { printf "%s\n" "Error: Given path '$PREFIX_STUB_HINT' is not found." >&2 ; exit 78 ; } ;
# Automation script path
# Full Regex: ^(?<dirname>(?<dirNum>[0-9]+)(?:[x0-9])?(?<prefix>\-[^\/]*))(?:\/)(?<filename>(?<fileNum>(?P=dirNum)(?:[0-9]?))(?:(?P=prefix)(?<baseName>[^\/]*)\.sh))$
EXAMPLE_CMD_HINT="${PREFIX_STUB_HINT:-.}/${EXAMPLE_NAME_HINT:-}.sh" ;
EXAMPLE_CMD_PATH=$(find ${PREFIX_STUB_HINT:-} -type f -iname "$EXAMPLE_NAME_HINT.sh" -print 2>/dev/null) ;
test -f "${EXAMPLE_CMD_PATH:-}" || { printf "%s\n" "Error: The path '${EXAMPLE_CMD_PATH:-}' is not found." >&2 ; exit 125 ; } ;
#test -x "${EXAMPLE_CMD_PATH:-}" || { printf "%s\n" "Error: Bad path '${EXAMPLE_CMD_PATH:-}' is not executable." >&2 ; exit 125 ; } ;

# Now, we can re-configure based on verified match
#
PREFIX_STUB=$(dirname "${EXAMPLE_CMD_PATH}") ;
{ test -d ${PREFIX_STUB:-} ;} || { printf "%s\n" "Error: Expected directory '$PREFIX_STUB' is not found." >&2 ; exit 78 ; } ;
EXAMPLE_DIR=$(basename "${PREFIX_STUB:-}") ;
EXAMPLE_NAME=$(basename -s .sh "${EXAMPLE_CMD_PATH}") ;

# Artifact paths (outputs)
TRANSCRIPT="${PREFIX_STUB:-.}/${EXAMPLE_NAME:-}.txt" ;
FORMATTED_DOC="${PREFIX_STUB:-.}/${EXAMPLE_NAME:-}.md" ;
test -f "Makefile" || { printf "%s\n" "Error: Required file './Makefile' is not found." >&2 ; exit 126 ; } ;
# see-also Makefile
REPO_NAME=$(basename `git rev-parse --show-toplevel`)
VENV_NAME="venv/${REPO_NAME:-demo}"

cleanup() {
    printf "\nDeactivating demo environment...\n" ;
    deactivate 2>/dev/null || : ;
    printf "\nCelaning-up demo environment...\n" ;
    make local-uninstall 2>/dev/null || : ;
    make un-setup >/dev/null 2>/dev/null || : ;
}
trap cleanup EXIT

# TODO: add validation checks (files missing? etc.)

printf '%s\n' "Setting up example environment..." ;

# subprocess isolation
(
    set -euo pipefail
    make setup-examples
    make local-install
    # Run examples
) || {
    make un-setup 2>/dev/null || true
    exit $?
}

printf '%s\n' "Activating example environment..."

# subprocess isolation
{
    source ./"${VENV_NAME}/bin/activate"
    printf '%s\n' "Running: ${EXAMPLE_CMD_PATH:-}" ;
    # run the example
    source "${EXAMPLE_CMD_PATH}" | tee "$TRANSCRIPT" ;
} || {
    deactivate 2>/dev/null || true
    exit $?
}

make un-setup >/dev/null ;

printf '%s\n' "Output complete: $TRANSCRIPT"
printf '%s\n' "Preview it with: tail -n+1 $TRANSCRIPT"

# format the example for docs
printf '%s\n' "Formatting example..." ;

printf '%s\n\n' "[Example ${EXAMPLE_NUM:-}](./docs/examples/${EXAMPLE_DIR:-}/${EXAMPLE_NAME:-}.md)" > "${FORMATTED_DOC}" ;
printf '%sconsole\n' $'```' >> "${FORMATTED_DOC}" ;
tail -n +1 $TRANSCRIPT | sed '1d;$d' >> "${FORMATTED_DOC}" ;
printf '\n%s\n' $'```' >> "${FORMATTED_DOC}" ;

printf "\n" ;
