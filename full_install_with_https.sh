#!/bin/bash

# Color settings for messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}Telegram Premium Subscription Bot Full Installation with HTTPS${NC}"
echo -e "${BLUE}=========================================${NC}"

# Install git if not installed
if ! command -v git &> /dev/null; then
    echo -e "\n${YELLOW}Git not found. Installing git...${NC}"
    apt-get update
    apt-get install -y git
fi

# Create a directory for the bot
echo -e "\n${YELLOW}Creating installation directory...${NC}"
mkdir -p ~/telegram-bot
cd ~/telegram-bot

# Clone the repository
echo -e "\n${YELLOW}Cloning the repository...${NC}"
git clone https://github.com/asanseir724/56654456.git .

# Make scripts executable
echo -e "\n${YELLOW}Making scripts executable...${NC}"
chmod +x *.sh

# Run the installation script
echo -e "\n${YELLOW}Running installation script...${NC}"
./one_click_install_en.sh

# Setup HTTPS
echo -e "\n${YELLOW}Setting up HTTPS...${NC}"
./setup_https.sh

echo -e "\n${GREEN}Installation completed with HTTPS setup!${NC}"
echo -e "${BLUE}The bot is installed in:${NC} $(pwd)"
echo -e "${BLUE}=========================================${NC}"