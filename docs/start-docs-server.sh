#!/bin/bash

# QuantumForge Documentation Server Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════╗"
echo "║   QuantumForge Documentation Server          ║"
echo "║   Port: 3002                                  ║"
echo "╚═══════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running in docs directory
if [ ! -f "mkdocs.yml" ]; then
    echo -e "${RED}Error: mkdocs.yml not found!${NC}"
    echo "Please run this script from the docs directory"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :3002 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}Warning: Port 3002 is already in use${NC}"
        echo "Do you want to kill the process using port 3002? (y/n)"
        read -r response
        if [ "$response" = "y" ]; then
            lsof -ti:3002 | xargs kill -9
            echo -e "${GREEN}Process killed${NC}"
        else
            echo "Please free port 3002 and try again"
            exit 1
        fi
    fi
}

# Function to install dependencies
install_deps() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt
    echo -e "${GREEN}Dependencies installed${NC}"
}

# Function to start development server
start_dev() {
    echo -e "${BLUE}Starting development server...${NC}"
    source venv/bin/activate
    mkdocs serve --dev-addr=0.0.0.0:3002
}

# Function to build static site
build_static() {
    echo -e "${BLUE}Building static site...${NC}"
    source venv/bin/activate
    mkdocs build --clean
    echo -e "${GREEN}Static site built in ./site/${NC}"
}

# Function to start with Docker
start_docker() {
    echo -e "${BLUE}Starting with Docker...${NC}"
    docker-compose -f docker-compose.docs.yml up -d
    echo -e "${GREEN}Docker container started${NC}"
    echo -e "${BLUE}View logs: docker-compose -f docker-compose.docs.yml logs -f${NC}"
}

# Function to stop Docker
stop_docker() {
    echo -e "${BLUE}Stopping Docker containers...${NC}"
    docker-compose -f docker-compose.docs.yml down
    echo -e "${GREEN}Docker containers stopped${NC}"
}

# Main menu
show_menu() {
    echo ""
    echo "Select an option:"
    echo "1) Start development server (localhost)"
    echo "2) Build static site"
    echo "3) Start with Docker"
    echo "4) Stop Docker containers"
    echo "5) Install/Update dependencies"
    echo "6) Exit"
    echo ""
    read -p "Enter choice [1-6]: " choice
}

# Check port
check_port

# Main loop
while true; do
    show_menu
    case $choice in
        1)
            install_deps
            start_dev
            ;;
        2)
            install_deps
            build_static
            ;;
        3)
            start_docker
            echo ""
            echo -e "${GREEN}Documentation server is running!${NC}"
            echo -e "${BLUE}URL: http://localhost:3002${NC}"
            break
            ;;
        4)
            stop_docker
            ;;
        5)
            install_deps
            ;;
        6)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
done

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Documentation Server Started Successfully!   ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📚 Documentation: http://localhost:3002${NC}"
echo -e "${BLUE}🔍 Search: http://localhost:3002/search${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

