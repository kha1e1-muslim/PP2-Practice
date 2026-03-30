-- procedures.sql
-- Create contacts table if it doesn't exist
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster searches
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);

-- Procedure: Insert or update contact (upsert)
CREATE OR REPLACE PROCEDURE upsert_contact(
    p_name VARCHAR,
    p_phone VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM contacts WHERE name = p_name) THEN
        UPDATE contacts 
        SET phone = p_phone, updated_at = CURRENT_TIMESTAMP
        WHERE name = p_name;
        RAISE NOTICE 'Contact % updated successfully', p_name;
    ELSE
        INSERT INTO contacts(name, phone) 
        VALUES(p_name, p_phone);
        RAISE NOTICE 'Contact % inserted successfully', p_name;
    END IF;
END;
$$;

-- Procedure: Insert contact with validation
CREATE OR REPLACE PROCEDURE insert_contact_if_valid(
    p_name VARCHAR,
    p_phone VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    -- Validate phone number
    IF NOT is_valid_phone(p_phone) THEN
        CALL add_invalid_contact(p_name, p_phone, 'Invalid phone number format');
        RAISE NOTICE 'Invalid phone number for %: %', p_name, p_phone;
        RETURN;
    END IF;
    
    -- Validate name is not empty
    IF p_name IS NULL OR TRIM(p_name) = '' THEN
        CALL add_invalid_contact(p_name, p_phone, 'Name cannot be empty');
        RAISE NOTICE 'Invalid name for %', p_name;
        RETURN;
    END IF;
    
    -- Insert the contact
    INSERT INTO contacts(name, phone) 
    VALUES(p_name, p_phone)
    ON CONFLICT (name) DO UPDATE 
    SET phone = EXCLUDED.phone, updated_at = CURRENT_TIMESTAMP;
    
    RAISE NOTICE 'Contact % inserted/updated successfully', p_name;
END;
$$;

-- Procedure: Delete contact by name or phone
CREATE OR REPLACE PROCEDURE delete_contact(
    p_identifier VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Try to delete by name first
    DELETE FROM contacts WHERE name = p_identifier;
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    -- If no rows deleted, try by phone
    IF v_deleted_count = 0 THEN
        DELETE FROM contacts WHERE phone = p_identifier;
        GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    END IF;
    
    IF v_deleted_count > 0 THEN
        RAISE NOTICE 'Deleted % contact(s) with identifier: %', v_deleted_count, p_identifier;
    ELSE
        RAISE NOTICE 'No contact found with identifier: %', p_identifier;
    END IF;
END;
$$;

-- Procedure: Bulk delete contacts by pattern
CREATE OR REPLACE PROCEDURE delete_contacts_by_pattern(
    p_pattern VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM contacts 
    WHERE name ILIKE '%' || p_pattern || '%'
       OR phone ILIKE '%' || p_pattern || '%';
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % contact(s) matching pattern: %', v_deleted_count, p_pattern;
END;
$$;

-- Procedure: Clean up old contacts (older than specified days)
CREATE OR REPLACE PROCEDURE cleanup_old_contacts(
    p_days INTEGER
)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM contacts 
    WHERE updated_at < CURRENT_TIMESTAMP - (p_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RAISE NOTICE 'Deleted % contact(s) older than % days', v_deleted_count, p_days;
END;
$$;

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS update_contacts_updated_at ON contacts;
CREATE TRIGGER update_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();