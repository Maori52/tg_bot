DO $$
BEGIN

    IF NOT EXISTS (SELECT * FROM pg_replication_slots WHERE slot_name = 'replication_slot') THEN
        PERFORM pg_create_physical_replication_slot('replication_slot');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'phone_numbers') THEN
        CREATE TABLE phone_numbers (
            ID SERIAL PRIMARY KEY,
            phone_number VARCHAR(255) NOT NULL
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'emails') THEN
        CREATE TABLE emails (
            ID SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL
        );
    END IF;

    GRANT SELECT ON ALL TABLES IN SCHEMA public TO replica_user;
END $$;
