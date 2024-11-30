# gacha-world

Catching gacha for fun

## Usage

### Environment

Rename `.env.example` to `.env` and change the values as needed.

### HTTPS

Create a self-signed certificate:

```bash
mkdir certs
openssl req -x509 -newkey rsa:4096 -nodes -out certs/player-cert.pem -keyout certs/player-key.pem -days 365 -subj "/"
openssl req -x509 -newkey rsa:4096 -nodes -out certs/auction-cert.pem -keyout certs/auction-key.pem -days 365 -subj "/"
openssl req -x509 -newkey rsa:4096 -nodes -out certs/gateway-cert.pem -keyout certs/gateway-key.pem -days 365 -subj "/"
```
