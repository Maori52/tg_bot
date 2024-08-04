#!/bin/bash
set -e
echo "ADD HOST TO PG_HBA.CONF"
echo "host    replication     all             0.0.0.0/0                 md5" >> "$PGDATA/pg_hba.conf"
echo "host    all             all             0.0.0.0/0                scram-sha-256" >> "$PGDATA/pg_hba.conf"
echo "host    replication     all             0.0.0.0/0                scram-sha-256" >> "$PGDATA/pg_hba.conf"