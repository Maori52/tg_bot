#!/bin/bash
set -e
mkdir /var/lib/postgresql/data/archive
chown postgres:postgres /var/lib/postgresql/data/archive
echo "ADD HOST TO PG_HBA.CONF"
echo "host    replication     replica_user      0.0.0.0/0               md5" >> "$PGDATA/pg_hba.conf"
