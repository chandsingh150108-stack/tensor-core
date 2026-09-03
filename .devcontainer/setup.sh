#!/usr/bin/env bash
# Devcontainer setup: install dependencies for building and testing.
set -euo pipefail

echo "Installing Chromium..."
sudo apt-get update
sudo apt-get install -y chromium

echo "Setup complete."
