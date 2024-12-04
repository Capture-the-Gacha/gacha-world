# gacha-world

Catching gacha for fun

## Usage

### Set up Environment

Rename `.env.example` to `.env` and change the values as needed.

### Create HTTPS certificates & JWT Secrets

Create self-signed certificates + private and public key for JWT:

```bash
chmod +x init.sh
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
chmod +x test.sh
./test.sh
cd -
```

Player service:

```bash
cd services/Player
chmod +x test.sh
./test.sh
cd -
```

### Integration Testing (ATTENTION: This will remove all data in the volumes)

Auth service:

```bash
cd tests/integration
chmod +x auth_test.sh
./auth_test.sh
cd -
```

Player service:

```bash
cd tests/integration
chmod +x player_test.sh
./player_test.sh
cd -
```
