#!/bin/bash

THIS_DIR=$(dirname $0)
THIS_PORT=""

if [[ $1 == "-h" || $1 == "--help" ]]; then
    echo "Usage: $(basename $0) server_port"
    echo "  Start the BattleSnake server (i.e. 'server.py') in the current directory."
    echo "  If the script detects that a server on the same port is active,"
    echo "  you'll be given the option to attempt to kill it before starting."
    echo "  Minimum required options:"
    echo "      -p|--port server_port : The port number to expose the snake server on."
    echo "  Other options belonging to 'server.py' can be provided as well."
    exit 0
fi

while (( "$#" )); do
    case "$1" in
        -p|--port)
            THIS_PORT=$2
            break
            ;;
    esac
done

if [[ ! ( "${THIS_PORT}" =~ ^[0-9]+$ ) ]]; then
    echo "The port must be a number, not: '${THIS_PORT}'" >&2
    exit 1
fi

THIS_VENV=${THIS_DIR}/venv
THIS_SERVER=${THIS_DIR}/server.py
THIS_PIP_REQ=${THIS_DIR}/requirements.txt
THIS_PS_SIG=".*python3 .*$(basename ${THIS_SERVER}).*(-p|-port)\s${THIS_PORT}.*$"

set -e

if [[ ! -f ${THIS_SERVER} ]]; then
    echo "Unable to find server file at: '$(readlink -f ${THIS_SERVER})'" >&2
    echo "Make sure you've deployed your snake server." >&2
    exit 1
elif [[ ! -d ${THIS_VENV} ]]; then
    echo "No python 'venv' detected, will create it now and activate it..."

    if [[ ! -f ${THIS_PIP_REQ} ]]; then
        echo "Unable to pip requirements for venv: '$(readlink -f ${THIS_PIP_REQ})'" >&2
        echo "Make sure you've deployed your snake server." >&2
        exit 1
    fi

    python3 -m venv ${THIS_VENV}
    source ${THIS_VENV}/bin/activate
    pip install -r ${THIS_PIP_REQ}
    echo "Python 'venv' created and activated."
else
    source ${THIS_VENV}/bin/activate
fi

EXISTING_PS_ID=$(ps -f -u ${USER} | grep -E "${THIS_PS_SIG}" | awk '{print $2}')

if [[ "${EXISTING_PS_ID}" != "" ]]; then
    ps -f --pid ${EXISTING_PS_ID}
    read -p "Server process ${EXISTING_PS_ID} already running on that port, kill it? (Y/N) " KILL_SVR
    if [[ "${KILL_SVR}" == "Y" ]]; then
        kill ${EXISTING_PS_ID}
    else
        echo "Aborting."
        exit 1
    fi
fi

python3 ${THIS_SERVER} $@
