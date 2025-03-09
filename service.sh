#!/bin/bash
API_ROOT=$(dirname $(realpath "${0}"))
SERVICE_TEMPLATE="${API_ROOT}/service.template"
SERVICE_NAME="createveai-api-server"
SERVICE_USER=$(whoami)
SERVICE_GROUP=$(groups | awk '{print $1}')
# Check for ability to sudo
if [[ ! $(sudo -n true 2>/dev/null) ]]; then
    echo "This script requires sudo"
    exit 1
fi
# Check for install or uninstall options, if not print help
if [[ "$1" == "install" ]]; then
    # Check for -U and -G options
    while getopts "U:G:" opt; do
        case $opt in
            U)
                SERVICE_USER=$OPTARG
                ;;
            G)
                SERVICE_GROUP=$OPTARG
                ;;
            \?)
                echo "Invalid option: -$OPTARG" >&2
                ;;
        esac
    done
    # Create service file
    sed -e "s|{API_ROOT}|${API_ROOT}|g" \
        -e "s|{SERVICE_USER}|${SERVICE_USER}|g" \
        -e "s|{SERVICE_GROUP}|${SERVICE_GROUP}|g" \
        "${SERVICE_TEMPLATE}" > "${SERVICE_NAME}.service"
    # Check for existing service#
    if [[ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]]; then
        # Ask to stop and disable
        read -p "Service already exists, stop and disable? [Y/n]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            sudo systemctl stop "${SERVICE_NAME}.service"
            sudo systemctl disable "${SERVICE_NAME}.service"
        else
            echo "Service already exists, exiting"
            exit 0
        fi

    fi
    # Copy service file to /etc/systemd/system
    sudo cp "${SERVICE_NAME}.service" "/etc/systemd/system/${SERVICE_NAME}.service"
    # Set correct owner
    sudo chown root:root "/etc/systemd/system/${SERVICE_NAME}.service"
    # Set correct permissions
    sudo chmod 644 "/etc/systemd/system/${SERVICE_NAME}.service"
    # Reload systemd
    sudo systemctl daemon-reload
    # Ask to enable and start
    read -p "Enable and start service? [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        sudo systemctl enable "${SERVICE_NAME}.service"
        sudo systemctl start "${SERVICE_NAME}.service"
    fi

elif [[ "$1" == "uninstall" ]]; then
    # Check if sure
    read -p "Are you sure you want to uninstall the service? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting"
        exit 0
    fi
    # Stop and disable service
    sudo systemctl stop "${SERVICE_NAME}.service"
    sudo systemctl disable "${SERVICE_NAME}.service"
    # Remove service file
    sudo rm "/etc/systemd/system/${SERVICE_NAME}.service"
    # Reload systemd
    sudo systemctl daemon-reload
    # Remove service file
    rm "${SERVICE_NAME}.service"
  
else
  echo "Usage: $0 [install|uninstall] -U [username] -G [groupname]"
  echo "By default, installs as createveai-api-server uses the logged-in user and group, and enables"
  exit 1
fi