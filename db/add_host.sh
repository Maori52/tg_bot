#!/bin/bash
set -e

mkdir -p /var/lib/postgresql/data/archive

chown postgres:postgres /var/lib/postgresql/data/archive

echo "ADD HOST TO PG_HBA.CONF"
if ! grep -q "host    replication     replica_user      0.0.0.0/0               md5" "$PGDATA/pg_hba.conf"; then
    echo "host    replication     replica_user      0.0.0.0/0               md5" >> "$PGDATA/pg_hba.conf"

    echo "Line added to pg_hba.conf"
else
    echo "Line already exists in pg_hba.conf"
fi

echo "local   all   postgres   trust" >> "$PGDATA/pg_hba.conf"