#!/bin/bash

# QuantumForge Documentation Server
# Quick start script for port 3002

set -e

echo "🚀 Starting QuantumForge Documentation Server..."
echo ""

# Navigate to docs directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting server on http://0.0.0.0:3002"
echo "📖 Access documentation at: http://localhost:3002"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start MkDocs server
mkdocs serve --dev-addr=0.0.0.0:3002

