#!/bin/bash

# Nginx Configuration Fix Script
# This script fixes common Nginx configuration issues

echo "🔧 Fixing Nginx configuration..."

# Get the server IP address
SERVER_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || hostname -I | awk '{print $1}')
echo "📡 Detected server IP: $SERVER_IP"

# Stop Nginx first
echo "🛑 Stopping Nginx..."
sudo systemctl stop nginx

# Remove existing configuration
echo "🗑️ Removing existing configuration..."
sudo rm -f /etc/nginx/sites-enabled/michi-robot
sudo rm -f /etc/nginx/sites-enabled/default

# Create a simple, working Nginx configuration
echo "⚙️ Creating simple Nginx configuration..."
sudo tee /etc/nginx/sites-available/michi-robot << EOF
server {
    listen 80;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;

    # SSL Configuration (self-signed for IP-only setup)
    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
    
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

# Create self-signed certificate if it doesn't exist
if [ ! -f "/etc/ssl/certs/nginx-selfsigned.crt" ]; then
    echo "🔐 Creating self-signed certificate..."
    sudo mkdir -p /etc/ssl/private
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/nginx-selfsigned.key \
        -out /etc/ssl/certs/nginx-selfsigned.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$SERVER_IP"
fi

# Enable the site
echo "🔗 Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/michi-robot /etc/nginx/sites-enabled/

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid!"
    
    # Start Nginx
    echo "🚀 Starting Nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    echo "✅ Nginx is now running!"
    echo "🌐 Your server should be accessible at: https://$SERVER_IP"
else
    echo "❌ Nginx configuration test failed!"
    echo "📋 Configuration file contents:"
    sudo cat /etc/nginx/sites-available/michi-robot
    exit 1
fi 