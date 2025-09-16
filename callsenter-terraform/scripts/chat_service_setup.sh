#!/bin/bash

# Update the system
sudo apt-get update -y

# Install necessary packages
sudo apt-get install -y python3 python3-pip git

# Clone the CallSenter repository
git clone https://github.com/yourusername/CallSenter.git

# Navigate to the chat_service directory
cd CallSenter/chat_service

# Install required Python packages
pip3 install -r requirements.txt

# Start the Uvicorn server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &