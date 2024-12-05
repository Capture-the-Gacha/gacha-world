#!/bin/bash

# Create certs directory if it doesn't exist
test -d certs || mkdir certs

# Change to certs directory
cd certs

    # Create certificates and keys only if they do not exist
    echo "- Checking for existing certificates and keys -"
    test -f player-cert.pem || { echo "    Creating Player certificates..."; openssl req -x509 -newkey rsa:4096 -nodes -out player-cert.pem -keyout player-key.pem -days 365 -subj "/" > /dev/null 2>&1; }
    test -f auction-cert.pem || { echo "    Creating Auction certificates..."; openssl req -x509 -newkey rsa:4096 -nodes -out auction-cert.pem -keyout auction-key.pem -days 365 -subj "/" > /dev/null 2>&1; }
    test -f gateway-cert.pem || { echo "    Creating Gateway certificates..."; openssl req -x509 -newkey rsa:4096 -nodes -out gateway-cert.pem -keyout gateway-key.pem -days 365 -subj "/" > /dev/null 2>&1; }
    test -f admin-gateway-cert.pem || { echo "    Creating Admin Gateway certificates..."; openssl req -x509 -newkey rsa:4096 -nodes -out admin-gateway-cert.pem -keyout admin-gateway-key.pem -days 365 -subj "/" > /dev/null 2>&1; }
    test -f gacha-cert.pem || { echo "    Creating Gacha certificates..."; openssl req -x509 -newkey rsa:4096 -nodes -out gacha-cert.pem -keyout gacha-key.pem -days 365 -subj "/" > /dev/null 2>&1; }
    test -f auth-cert.pem || { echo "    Creating Auth certificates..."; openssl req -x509 -newkey rsa:4096 -nodes -out auth-cert.pem -keyout auth-key.pem -days 365 -subj "/" > /dev/null 2>&1; }
    echo "All certificates and keys have been created."

# Set permissions
chmod 0444 ./*

# Return to the previous directory
cd ..

echo ""

# Create secrets directory if it doesn't exist
test -d secrets || mkdir secrets

# Change to secrets directory
cd secrets

    # Create JWT keys only if they do not exist
    echo "- Checking for existing JWT keys -"
    test -f jwt-private-key.pem || { echo "    Creating JWT private key..."; openssl genpkey -algorithm RSA -out jwt-private-key.pem -pkeyopt rsa_keygen_bits:2048 > /dev/null 2>&1; }
    test -f jwt-public-key.pub || { echo "    Creating JWT public key..."; openssl rsa -in jwt-private-key.pem -pubout -out jwt-public-key.pub > /dev/null 2>&1; }
    echo "All JWT keys have been created."

# Return to the previous directory
cd ..