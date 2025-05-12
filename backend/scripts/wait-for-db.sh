#!/bin/sh
until pg_isready -h db -p 5432 -U postgres; do
  echo "Waiting for database..."
  sleep 2
done
echo "Database ready!"
