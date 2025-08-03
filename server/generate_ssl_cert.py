#!/usr/bin/env python3
"""
Simple script to generate self-signed SSL certificates for HTTPS
Run this script once to create the certificates needed for HTTPS
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_self_signed_cert():
    """Generate self-signed SSL certificate and private key"""
    
    # Create certificates directory if it doesn't exist
    cert_dir = Path(__file__).parent / "ssl_certs"
    cert_dir.mkdir(exist_ok=True)
    
    cert_path = cert_dir / "cert.pem"
    key_path = cert_dir / "key.pem"
    
    # Check if certificates already exist
    if cert_path.exists() and key_path.exists():
        print("SSL certificates already exist!")
        print(f"Certificate: {cert_path}")
        print(f"Private key: {key_path}")
        return str(cert_path), str(key_path)
    
    print("Generating self-signed SSL certificates...")
    
    try:
        # Generate private key
        subprocess.run([
            "openssl", "genrsa", "-out", str(key_path), "2048"
        ], check=True, capture_output=True)
        
        # Generate certificate
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", str(key_path),
            "-out", str(cert_path), "-days", "365", "-subj",
            "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        ], check=True, capture_output=True)
        
        print("✅ SSL certificates generated successfully!")
        print(f"Certificate: {cert_path}")
        print(f"Private key: {key_path}")
        print("\n⚠️  Note: These are self-signed certificates.")
        print("   Browsers will show a security warning.")
        print("   For production, use certificates from a trusted CA.")
        
        return str(cert_path), str(key_path)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating certificates: {e}")
        print("Make sure OpenSSL is installed on your system.")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL:")
        print("   Ubuntu/Debian: sudo apt-get install openssl")
        print("   CentOS/RHEL: sudo yum install openssl")
        print("   macOS: brew install openssl")
        sys.exit(1)

if __name__ == "__main__":
    cert_path, key_path = generate_self_signed_cert()
    print(f"\nCertificate paths for your server:")
    print(f"Cert: {cert_path}")
    print(f"Key: {key_path}") 