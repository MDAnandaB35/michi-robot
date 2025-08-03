#!/bin/bash

# HTTPS Deployment Script for EC2
# This script sets up HTTPS for your Quart server using Nginx and Let's Encrypt

set -e  # Exit on any error

echo "🚀 Starting HTTPS deployment for Michi Robot..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx configuration
echo "⚙️ Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/michi-robot << EOF
server {
    listen 80;
    server_name 18.142.229.32;
    
    # Redirect all HTTP traffic to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 18.142.229.32;

    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/18.142.229.32/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/18.142.229.32/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Quart application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Handle large file uploads
    client_max_body_size 10M;
}
EOF

# Enable the site
echo "🔗 Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/michi-robot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Start Nginx
echo "🚀 Starting Nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

# Get SSL certificate using Let's Encrypt
echo "🔐 Obtaining SSL certificate..."
sudo certbot --nginx -d 18.142.229.32 --non-interactive --agree-tos --email your-email@example.com

# Set up automatic renewal
echo "🔄 Setting up automatic certificate renewal..."
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -

# Create systemd service for your Quart app
echo "📋 Creating systemd service for Quart app..."
sudo tee /etc/systemd/system/michi-robot.service << EOF
[Unit]
Description=Michi Robot Quart Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/michi-ui/server
Environment=PATH=/home/ubuntu/michi-ui/server/venv/bin
ExecStart=/home/ubuntu/michi-ui/server/venv/bin/python beta.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start the service
echo "🔄 Reloading systemd and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable michi-robot
sudo systemctl start michi-robot

# Check status
echo "📊 Checking service status..."
sudo systemctl status michi-robot --no-pager

echo "✅ HTTPS deployment completed!"
echo "🌐 Your server should now be accessible at: https://18.142.229.32"
echo "📝 Don't forget to update your frontend to use HTTPS URLs!" 