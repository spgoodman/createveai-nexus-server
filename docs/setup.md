# Setup Guide

This guide provides instructions for installing and configuring the Createve.AI Nexus Server.

## Installation

1.  Clone this repo:

    ```bash
    git clone https://github.com/spgoodman/createveai-nexus-server.git
    cd createveai-nexus-server
    ```

2.  Run `start.sh` to set up a Python virtual environment and start the server:

    ```bash
    chmod +x start.sh
    ./start.sh
    ```

## Running as a Service

### Docker Compose (Recommended)

Use Docker Compose to start the server as a Docker container:

```bash
docker-compose up -d
```

### Systemd (Ubuntu)

Alternatively, use `service.sh` to install as a systemd service on Ubuntu:

```bash
# Install as service
./service.sh install -U user -G group

# Uninstall service
./service.sh uninstall
```

## Command Line Options

The server can be started with the following command line options:

```bash
python main.py [--config CONFIG_PATH] [--host HOST] [--port PORT] [--reload]
