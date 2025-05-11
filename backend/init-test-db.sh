#!/bin/bash
set -e

# Check if POSTGRES_USER and POSTGRES_DB are set (they are used by the main entrypoint)
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ]; then
  echo "POSTGRES_USER and POSTGRES_DB must be set"
  exit 1
fi

# The main entrypoint script of the postgres image will create POSTGRES_DB.
# We are running this script after that, or alongside it, to create an additional test database.
# We connect to the default 'postgres' database or the already created POSTGRES_DB to issue the CREATE DATABASE command.

TEST_DB_NAME="duelo_de_plumas_test"

echo "Attempting to create test database: $TEST_DB_NAME"

# Use psql to create the test database if it doesn't exist
# Connect to the maintenance database (postgres or the one specified by POSTGRES_DB)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE $TEST_DB_NAME'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$TEST_DB_NAME')\gexec
EOSQL

if [ $? -eq 0 ]; then
  echo "Test database '$TEST_DB_NAME' created successfully or already exists."
else
  echo "Failed to create test database '$TEST_DB_NAME'. Check logs."
  exit 1
fi

# Optionally, grant privileges if your test user is different or needs specific grants
# psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$TEST_DB_NAME" <<-EOSQL
#     GRANT ALL PRIVILEGES ON DATABASE $TEST_DB_NAME TO $POSTGRES_USER;
# EOSQL
# echo "Privileges granted on $TEST_DB_NAME to $POSTGRES_USER." 