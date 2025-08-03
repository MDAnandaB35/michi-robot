# SSL Protocol Error Troubleshooting Guide

## Problem: `net::ERR_SSL_PROTOCOL_ERROR` when accessing EC2 server

### Quick Fixes (Try these first):

#### 1. **Use HTTP instead of HTTPS**

If your server doesn't have SSL configured, access it via HTTP:

```
http://your-ec2-public-ip:5000
```

NOT:

```
https://your-ec2-public-ip:5000  ❌
```

#### 2. **Check EC2 Security Group**

- Go to AWS Console → EC2 → Security Groups
- Find your instance's security group
- Add inbound rule:
  - Type: Custom TCP
  - Port: 5000
  - Source: 0.0.0.0/0 (or your specific IP)

#### 3. **Verify Server is Running**

SSH into your EC2 instance and check:

```bash
# Check if server is running
ps aux | grep python

# Check if port 5000 is listening
netstat -tlnp | grep 5000

# Check server logs
tail -f /var/log/your-app.log
```

### SSL Solutions:

#### Option A: Generate Self-Signed Certificate (Development)

```bash
# On your EC2 instance
cd /path/to/your/server
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

Then run the SSL server:

```bash
python ssl_server.py
```

#### Option B: Use Let's Encrypt (Production)

1. Install Certbot:

```bash
sudo apt update
sudo apt install certbot
```

2. Get certificate:

```bash
sudo certbot certonly --standalone -d your-domain.com
```

3. Update your server to use the certificates:

```python
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('/etc/letsencrypt/live/your-domain.com/fullchain.pem',
                       '/etc/letsencrypt/live/your-domain.com/privkey.pem')
```

#### Option C: Use Nginx as Reverse Proxy

1. Install Nginx:

```bash
sudo apt install nginx
```

2. Configure Nginx:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Common Issues:

#### 1. **Browser Security Warning**

- Self-signed certificates will show security warnings
- Click "Advanced" → "Proceed to site" (development only)
- For production, use proper certificates

#### 2. **Port Already in Use**

```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill the process
sudo kill -9 <PID>
```

#### 3. **Firewall Issues**

```bash
# Check UFW status
sudo ufw status

# Allow port 5000
sudo ufw allow 5000
```

#### 4. **Domain Name Issues**

- Make sure your domain points to your EC2 public IP
- Check DNS propagation: https://www.whatsmydns.net/

### Testing Your Server:

#### Test HTTP:

```bash
curl http://your-ec2-public-ip:5000
```

#### Test HTTPS:

```bash
curl -k https://your-ec2-public-ip:5000
```

#### Test from Browser:

- Open Developer Tools (F12)
- Check Network tab for errors
- Look for CORS issues

### Production Checklist:

- [ ] Use proper SSL certificates (Let's Encrypt or paid)
- [ ] Configure security groups properly
- [ ] Set up domain name
- [ ] Use HTTPS redirect
- [ ] Configure proper CORS settings
- [ ] Set up monitoring and logging
- [ ] Configure backup and recovery

### Need Help?

1. Check server logs for specific errors
2. Verify network connectivity
3. Test with curl first, then browser
4. Check AWS CloudWatch for instance metrics
