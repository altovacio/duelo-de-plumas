#!/bin/bash

echo "Starting development environment..."
docker-compose down
docker-compose up --build -d