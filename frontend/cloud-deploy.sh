#!/bin/bash
# Script to deploy frontend to Cloud Run

# Navigate to frontend directory
cd ~/ChicagoBeerFinder/frontend

# Install dependencies and build
npm install
npm run build

# Create a temporary deployment directory
mkdir -p ~/deploy-frontend

# Copy the built files and Dockerfile
cp -r dist/* ~/deploy-frontend/
cat > ~/deploy-frontend/Dockerfile << 'EOF'
FROM nginx:alpine

COPY . /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

CMD sed -i -e 's/$PORT/'"$PORT"'/g' /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'
EOF

# Create nginx config
cat > ~/deploy-frontend/nginx.conf << 'EOF'
server {
    listen $PORT;
    server_name _;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    # Redirect API requests to the backend API
    location /api/ {
        proxy_pass https://beerfinder-api-877162996755.us-central1.run.app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Deploy to Cloud Run
cd ~/deploy-frontend
gcloud run deploy beerfinder-frontend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

echo "Frontend deployed successfully!"

# Clean up
rm -rf ~/deploy-frontend
