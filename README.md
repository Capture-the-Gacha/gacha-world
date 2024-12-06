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
cd docs/tests
./auth_unit_test.sh
cd -
```

Player service:

```bash
cd docs/tests
./player_unit_test.sh
cd -
```

Auction service:

```bash
cd docs/tests
./auction_unit_test.sh
cd -
```

### Integration Testing (ATTENTION: This will remove all data in the volumes)

Auth service:

```bash
cd docs/tests
./auth_integration_test.sh
cd -
```

Player service:

```bash
cd docs/tests
./player_integration_test.sh
cd -
```

Auction service:

```bash
cd docs/tests
./auction_integration_test.sh
cd -
```

### Security Testing

Run `bandit` and `pip-audit` using `docker-compose`:

```bash
docker compose run --rm bandit
docker compose run --rm pip-audit
```
