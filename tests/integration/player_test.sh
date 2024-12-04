#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' ../../.env | grep -v '^\s*$' | xargs)

# Bring down any existing Docker containers + volumes
docker compose down -v

# Bring up Docker containers with the latest build
docker compose up -d --quiet-pull --build

# Run Newman tests
newman run ../PlayerIntegrationTesting.postman_collection.json -e ../environment.postman_globals.json --insecure
NEWMAN_EXIT_CODE=$?

# Bring down Docker containers after tests
docker compose down -v

# Return the same response code as Newman
exit $NEWMAN_EXIT_CODE