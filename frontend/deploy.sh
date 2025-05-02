#!/bin/bash

# Build the frontend
cd frontend
npm install
npm run build

# Copy built frontend to backend static folder
mkdir -p ../static
cp -r dist/* ../static/

# Go back to project root
cd ..

# Start the Flask API with static file serving
python api2.py
