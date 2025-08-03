# HTTPS Setup for Michi Chatbot Server on EC2

This guide will help you set up HTTPS with self-signed certificates for your Michi chatbot server on EC2.

## Quick Setup (Recommended)

1. **Run the automated setup script:**

   ```bash
   chmod +x setup_https.sh
   ./setup_https.sh
   ```

2. **Start your server:**

   ```bash
   python3 beta.py
   ```

3. **Access your server:**
   - Get your EC2 public IP: `curl http://169.254.169.254/latest/meta-data/public-ipv4`
   - Access via: `https://YOUR_EC2_IP:5000`

## Manual Setup

If you prefer to do it manually:

1. **Install OpenSSL (if not already installed):**

   ```bash
   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install -y openssl

   # CentOS/RHEL
   sudo yum install -y openssl
   ```

2. **Generate SSL certificates:**

   ```bash
   python3 generate_ssl_cert.py
   ```

3. **Set proper permissions:**

   ```bash
   chmod 600 ssl_certs/key.pem
   chmod 644 ssl_certs/cert.pem
   ```

4. **Start your server:**
   ```bash
   python3 beta.py
   ```

## EC2 Security Group Configuration

Make sure your EC2 security group allows inbound traffic on port 5000:

1. Go to EC2 Console → Security Groups
2. Select your instance's security group
3. Add inbound rule:
   - Type: Custom TCP
   - Port: 5000
   - Source: 0.0.0.0/0 (or your specific IP range)

## Important Notes

⚠️ **Self-Signed Certificates:**

- Browsers will show security warnings (this is normal)
- You can click "Advanced" → "Proceed to site" to continue
- For production use, get certificates from a trusted CA (Let's Encrypt, etc.)

🔒 **Security:**

- Self-signed certificates provide encryption but not identity verification
- Suitable for development and internal use
- For public-facing production apps, use proper SSL certificates

## Troubleshooting

**Certificate not found error:**

- Make sure you ran `python3 generate_ssl_cert.py`
- Check that `ssl_certs/` directory exists with `cert.pem` and `key.pem`

**Permission denied:**

- Run `chmod 600 ssl_certs/key.pem` and `chmod 644 ssl_certs/cert.pem`

**OpenSSL not found:**

- Install OpenSSL using the commands above

**Can't access from browser:**

- Check EC2 security group allows port 5000
- Verify you're using `https://` not `http://`
- Accept the security warning in your browser
