#!/bin/bash
set -e
echo "ADD HOST TO PG_HBA.CONF"
echo "host    replication     all             0.0.0.0/0                scram-sha-256" >> "$PGDATA/pg_hba.conf"

if ! grep -q "host    replication     all             0.0.0.0/0                scram-sha-256" "$PGDATA/pg_hba.conf"; then
    echo "host    replication     all             0.0.0.0/0                scram-sha-256" >> "$PGDATA/pg_hba.conf"
    echo "Line added to pg_hba.conf"
else
    echo "Line already exists in pg_hba.conf"
fi

echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"

# Изменение метода аутентификации для пользователя postgres
echo "local   all   postgres   trust" >> "$PGDATA/pg_hba.conf"