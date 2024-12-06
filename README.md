# gacha-world

Catching gacha for fun

## Usage

### Set up Environment

Rename `.env.example` to `.env` and change the values as needed.

### Create HTTPS certificates & JWT Secrets

Create self-signed certificates + private and public key for JWT:

```bash
./init.sh
```

### Build the application

```bash
docker compose up -d --build
```

## Testing

### Unit Tests

Prepare the environment:

```bash
npm install -g newman
```

Auth service:

```bash
cd services/Auth
./test.sh
cd -
```

Player service:

```bash
cd services/Player
./test.sh
cd -
```

### Integration Testing (ATTENTION: This will remove all data in the volumes)

Auth service:

```bash
cd tests/integration
./auth_test.sh
cd -
```

Player service:

```bash
cd tests/integration
./player_test.sh
cd -
```

### Security Testing

Run `bandit` and `pip-audit` using `docker-compose`:

```bash
docker-compose run --rm bandit
docker-compose run --rm pip-audit
```
