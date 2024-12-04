# gacha-world

Catching gacha for fun

## Usage

### Environment

Rename `.env.example` to `.env` and change the values as needed.

### HTTPS

Create self-signed certificates:

```bash
test -d certs || mkdir certs &&
cd certs &&
openssl req -x509 -newkey rsa:4096 -nodes -out player-cert.pem -keyout player-key.pem -days 365 -subj "/" &&
openssl req -x509 -newkey rsa:4096 -nodes -out auction-cert.pem -keyout auction-key.pem -days 365 -subj "/" &&
openssl req -x509 -newkey rsa:4096 -nodes -out gateway-cert.pem -keyout gateway-key.pem -days 365 -subj "/" &&
openssl req -x509 -newkey rsa:4096 -nodes -out gacha-cert.pem -keyout gacha-key.pem -days 365 -subj "/" &&
openssl req -x509 -newkey rsa:4096 -nodes -out auth-cert.pem -keyout auth-key.pem -days 365 -subj "/" &&
chmod 0444 ./* &&
cd ..
```

### JWT Secret

Generate a private and public key for JWT:

```bash
test -d secrets || mkdir secrets;
cd secrets &&
openssl genpkey -algorithm RSA -out jwt-private-key.pem -pkeyopt rsa_keygen_bits:2048 &&
openssl rsa -in jwt-private-key.pem -pubout -out jwt-public-key.pub &&
cd ..
```

## Testing

### Unit Tests

Prepare the environment:

```bash
npm install -g newman
```

Auth service:

```bash
# Inside Auth service directory
export $(grep -v '^#' ../../.env | grep -v '^\s*$' | xargs) &&
docker compose down &&
docker compose up -d --quiet-pull --build &&
newman run ../../tests/AuthTesting.postman_collection.json -e ../../tests/environment.postman_globals.json --insecure &&
docker compose down
```

Player service:

```bash
# Inside Player service directory
export $(grep -v '^#' ../../.env | grep -v '^\s*$' | xargs) &&
docker compose down &&
docker compose up -d --quiet-pull --build &&
newman run ../../tests/PlayerTesting.postman_collection.json -e ../../tests/environment.postman_globals.json --insecure &&
docker compose down
```

### Integration Testing (ATTENTION: This will remove all data in the volumes)

Auth service:

```bash
export $(grep -v '^#' .env | grep -v '^\s*$' | xargs) &&
docker compose down -v &&
docker compose up -d --quiet-pull --build &&
newman run tests/AuthTesting.postman_collection.json -e tests/environment.postman_globals.json --insecure &&
docker compose down -v
```

Player service:

```bash
export $(grep -v '^#' .env | grep -v '^\s*$' | xargs) &&
docker compose down -v &&
docker compose up -d --quiet-pull --build &&
newman run tests/PlayerIntegrationTesting.postman_collection.json -e tests/environment.postman_globals.json --insecure &&
docker compose down -v
```
