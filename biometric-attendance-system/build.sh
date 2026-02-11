#!/usr/bin/env bash
# Render build script

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install wheel
pip install -r requirements.txt

echo "Creating necessary directories..."
mkdir -p static/uploads
mkdir -p database

echo "Build completed successfully!"
