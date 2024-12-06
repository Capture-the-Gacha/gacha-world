#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' ../../.env | grep -v '^\s*$' | xargs)

# Bring down any existing Docker containers
cd ../../services/Auction
docker compose down
# Bring up Docker containers with the latest build
docker compose up -d --quiet-pull --build

# Wait for API readiness
api_host="https://localhost:5000/openapi.json"
attempt_counter=0
max_attempts=10
sleep 5

while [ "$(curl -k -s -o /dev/null -w "%{http_code}" $api_host)" != "200" ]; do
    if [ ${attempt_counter} -eq ${max_attempts} ]; then
        echo "Max attempts reached. Exiting with error."
        exit 1
    fi

    echo "$api_host not reachable. Retrying in 5 seconds..."
    attempt_counter=$((attempt_counter+1))
    sleep 5
done

# Run Newman tests
cd ../../docs/tests/collections
newman run AuctionTesting.postman_collection.json -e environment.postman_globals.json --insecure
NEWMAN_EXIT_CODE=$?

# Bring down Docker containers after tests
cd ../../../services/Auction
docker compose down

# Return the same response code as Newman
exit $NEWMAN_EXIT_CODE
