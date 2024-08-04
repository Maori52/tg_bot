CREATE USER replica_user WITH REPLICATION ENCRYPTED PASSWORD '4173172';
SELECT pg_create_physical_replication_slot('replication_slot');

CREATE TABLE phone_numbers (
    ID SERIAL PRIMARY KEY,
    phone_number VARCHAR(255) NOT NULL
);

CREATE TABLE emails (
    ID SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);

GRANT SELECT ON ALL TABLES IN SCHEMA public TO replica_user;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET wal_log_hints = on;
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command='cp %p /var/lib/postgresql/data/archive/%f';
ALTER SYSTEM SET listen_addresses = '*';
ALTER SYSTEM SET hot_standby = on;