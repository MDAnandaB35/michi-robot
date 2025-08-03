@echo off
echo Generating SSL certificate for development...

REM Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

echo.
echo SSL certificate generated successfully!
echo Files created:
echo   - cert.pem (certificate)
echo   - key.pem (private key)
echo.
echo You can now run the SSL server with:
echo python ssl_server.py
echo.
echo Note: This is a self-signed certificate. Browsers will show a security warning.
echo For production, use a proper SSL certificate from a certificate authority.
pause 