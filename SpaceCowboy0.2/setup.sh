#!/bin/bash
set -e

# Update package lists
sudo apt update

# Install essential packages
sudo apt install -y build-essential mingw-w64 vim-common python3 python3-pip curl git

# Install Nim using choosenim (this script will download and install choosenim)
curl https://nim-lang.org/choosenim/init.sh -sSf | sh

# Source your profile to update PATH (or log out/in)
source ~/.profile

# Confirm installations
echo "Nim version:"
nim -v

echo "GCC cross-compiler location:"
which x86_64-w64-mingw32-gcc

echo "xxd location:"
which xxd

echo "Setup complete!"
