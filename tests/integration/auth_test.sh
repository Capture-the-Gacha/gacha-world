#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' ../../.env | grep -v '^\s*$' | xargs)

# Bring down any existing Docker containers + volumes
docker compose down -v

# Bring up Docker containers with the latest build
docker compose up -d --quiet-pull --build

# Run Newman tests
newman run ../AuthTesting.postman_collection.json -e ../environment.postman_globals.json --insecure

# Bring down Docker containers after tests
docker compose down -v

# Return the same response code as Newman
exit $?
