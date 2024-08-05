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
