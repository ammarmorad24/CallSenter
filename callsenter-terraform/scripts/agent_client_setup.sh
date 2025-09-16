#!/bin/bash
# agent_client_setup.sh - Startup script for the agent client EC2 instance

# Update the system
sudo apt-get update -y

# Install necessary packages
sudo apt-get install -y python3 python3-pip git

# Clone the CallSenter repository
git clone https://github.com/yourusername/callsenter.git

# Navigate to the agent_client directory
cd callsenter/agent_client

# Install required Python packages
pip3 install -r requirements.txt

# Start the Uvicorn server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &