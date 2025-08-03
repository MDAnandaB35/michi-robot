# SSL-enabled version of the server
import os
import ssl
from full_integration import app, core

if __name__ == '__main__':
    # SSL certificate paths (you'll need to generate these)
    cert_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'cert.pem'))
    key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'key.pem'))
    
    # Check if SSL certificates exist
    if os.path.exists(cert_path) and os.path.exists(key_path):
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        
        print("Starting server with SSL on https://0.0.0.0:5000")
        app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=False,
            ssl_context=context
        )
    else:
        print("SSL certificates not found. Starting server without SSL on http://0.0.0.0:5000")
        print("To enable SSL, generate certificates:")
        print("openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365")
        app.run(host="0.0.0.0", port=5000, debug=False) 