#!/bin/bash

# Zoom Assistant Manager Launcher Script
# This script can be double-clicked to run the application

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting Zoom Assistant Manager..."
echo "📁 Working directory: $SCRIPT_DIR"

# Function to check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ Error: Python is not installed or not in PATH"
        echo "Please install Python 3.7+ from https://python.org"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "✅ Python found: $PYTHON_CMD"
}

# Function to create virtual environment if it doesn't exist
setup_venv() {
    if [ ! -d ".venv" ]; then
        echo "📦 Creating virtual environment..."
        $PYTHON_CMD -m venv .venv
        if [ $? -ne 0 ]; then
            echo "❌ Failed to create virtual environment"
            read -p "Press Enter to exit..."
            exit 1
        fi
        echo "✅ Virtual environment created"
    else
        echo "✅ Virtual environment exists"
    fi
}

# Function to activate virtual environment
activate_venv() {
    source .venv/bin/activate
    if [ $? -ne 0 ]; then
        echo "❌ Failed to activate virtual environment"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "✅ Virtual environment activated"
}

# Function to install/upgrade pip
setup_pip() {
    echo "🔧 Ensuring pip is up to date..."
    python -m pip install --upgrade pip > /dev/null 2>&1
}

# Function to install required packages
install_requirements() {
    echo "📦 Installing required packages..."
    
    # Install requests if not already installed
    python -c "import requests" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "  Installing requests..."
        pip install requests
    else
        echo "  ✅ requests already installed"
    fi
    
    # Check if tkinter is available (usually comes with Python)
    python -c "import tkinter" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "  ⚠️  tkinter not found. On some Linux systems, you may need to install python3-tk"
        echo "     For Ubuntu/Debian: sudo apt-get install python3-tk"
        echo "     For CentOS/RHEL: sudo yum install tkinter"
    else
        echo "  ✅ tkinter available"
    fi
    
    echo "✅ All requirements checked"
}

# Function to run the application
run_app() {
    echo "🎯 Launching Zoom Assistant Manager..."
    echo ""
    python zoom_assistant_manager.py
    
    # Keep terminal open if there was an error
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Application exited with an error"
        read -p "Press Enter to exit..."
    fi
}

# Main execution
echo "=================================================="
echo "       Zoom Assistant Manager Launcher"
echo "=================================================="
echo ""

check_python
setup_venv
activate_venv
setup_pip
install_requirements
echo ""
run_app
