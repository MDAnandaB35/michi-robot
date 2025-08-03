#!/bin/bash

# HTTPS Deployment Script for EC2 (IP-only setup)
# This script sets up HTTPS for your Quart server using Nginx and Let's Encrypt

set -e  # Exit on any error

echo "🚀 Starting HTTPS deployment for Michi Robot (IP-only setup)..."

# Get the server IP address
SERVER_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || hostname -I | awk '{print $1}')
echo "📡 Detected server IP: $SERVER_IP"

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
    server_name $SERVER_IP;
    
    # Redirect all HTTP traffic to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $SERVER_IP;

    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/$SERVER_IP/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$SERVER_IP/privkey.pem;
    
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

# Get SSL certificate using Let's Encrypt (IP-only)
echo "🔐 Obtaining SSL certificate for IP address..."
echo "⚠️  Note: Let's Encrypt may not work with IP addresses. Trying anyway..."

# Try to get certificate for IP
if sudo certbot --nginx -d $SERVER_IP --non-interactive --agree-tos --email admin@example.com; then
    echo "✅ SSL certificate obtained successfully!"
else
    echo "⚠️  Let's Encrypt failed for IP address. This is expected."
    echo "🔧 Creating self-signed certificate for development..."
    
    # Create self-signed certificate
    sudo mkdir -p /etc/ssl/private
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/nginx-selfsigned.key \
        -out /etc/ssl/certs/nginx-selfsigned.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$SERVER_IP"
    
    # Update Nginx configuration to use self-signed certificate
    sudo sed -i "s|ssl_certificate /etc/letsencrypt/live/$SERVER_IP/fullchain.pem;|ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;|g" /etc/nginx/sites-available/michi-robot
    sudo sed -i "s|ssl_certificate_key /etc/letsencrypt/live/$SERVER_IP/privkey.pem;|ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;|g" /etc/nginx/sites-available/michi-robot
    
    # Reload Nginx
    sudo systemctl reload nginx
    echo "✅ Self-signed certificate created and configured!"
fi

# Set up automatic renewal (only if Let's Encrypt worked)
if [ -d "/etc/letsencrypt/live/$SERVER_IP" ]; then
    echo "🔄 Setting up automatic certificate renewal..."
    sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -
fi

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
echo "🌐 Your server should now be accessible at: https://$SERVER_IP"
echo "⚠️  Note: If using self-signed certificate, browsers will show a security warning."
echo "📝 Don't forget to update your frontend to use HTTPS URLs!"
echo "🔧 To accept self-signed certificate in browser, visit https://$SERVER_IP and accept the warning." 