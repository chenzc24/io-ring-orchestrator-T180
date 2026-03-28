#!/bin/bash
# AMS-IO-Agent Script Runner
# Automatically uses the correct Python environment with smolagents

# Detect AMS-IO-Agent location
if [ -z "$AMS_IO_AGENT_PATH" ]; then
    # Try default location
    DEFAULT_PATH="/home/chenzc_intern25/AMS-IO-Agent_processes_combined/AMS-IO-Agent"
    if [ -d "$DEFAULT_PATH" ]; then
        export AMS_IO_AGENT_PATH="$DEFAULT_PATH"
    else
        echo "❌ Error: AMS_IO_AGENT_PATH not set and default location not found"
        echo "Please set: export AMS_IO_AGENT_PATH=/path/to/AMS-IO-Agent"
        exit 2
    fi
fi

# Detect venv Python
VENV_PYTHON="$AMS_IO_AGENT_PATH/venv/bin/python3"

if [ -x "$VENV_PYTHON" ]; then
    # Use venv Python (has smolagents installed)
    exec "$VENV_PYTHON" "$@"
else
    # Fall back to system Python (may not have smolagents)
    echo "⚠️  Warning: venv not found at $AMS_IO_AGENT_PATH/venv"
    echo "   Using system Python (may fail if smolagents not installed)"
    exec python3 "$@"
fi
