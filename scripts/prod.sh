#!/bin/bash

echo "Starting production environment..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d 