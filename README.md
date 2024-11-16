# gacha-world

Catching gacha for fun

## Usage

### Environment

Rename `.env.example` to `.env` and change the values as needed.

### HTTPS

Create a self-signed certificate:

```bash
mkdir certs
openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365 -subj "/"
```
