#!/bin/bash

echo "🔧 Setting up HTTPS for Michi Chatbot Server on EC2"
echo "=================================================="

# Check if running on EC2
if curl -s http://169.254.169.254/latest/meta-data/instance-id > /dev/null 2>&1; then
    echo "✅ Running on EC2 instance"
else
    echo "⚠️  Not running on EC2 (or metadata service not available)"
fi

# Install OpenSSL if not present
if ! command -v openssl &> /dev/null; then
    echo "📦 Installing OpenSSL..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y openssl
    elif command -v yum &> /dev/null; then
        sudo yum install -y openssl
    else
        echo "❌ Could not install OpenSSL automatically. Please install it manually."
        exit 1
    fi
else
    echo "✅ OpenSSL is already installed"
fi

# Generate SSL certificates
echo "🔐 Generating SSL certificates..."
python3 generate_ssl_cert.py

# Set proper permissions for certificates
if [ -d "ssl_certs" ]; then
    echo "🔒 Setting secure permissions for certificates..."
    chmod 600 ssl_certs/key.pem
    chmod 644 ssl_certs/cert.pem
    echo "✅ Certificate permissions set"
fi

echo ""
echo "🎉 HTTPS setup complete!"
echo "=================================================="
echo "To start your server with HTTPS:"
echo "  python3 beta.py"
echo ""
echo "Your server will be available at:"
echo "  https://YOUR_EC2_PUBLIC_IP:5000"
echo ""
echo "⚠️  Important notes:"
echo "  - Browsers will show security warnings (normal for self-signed certs)"
echo "  - You can accept the warning to proceed"
echo "  - For production, use certificates from a trusted CA"
echo ""
echo "🔧 To get your EC2 public IP:"
echo "  curl http://169.254.169.254/latest/meta-data/public-ipv4" 