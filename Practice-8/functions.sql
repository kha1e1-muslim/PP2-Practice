
CREATE OR REPLACE FUNCTION search_contacts_by_pattern(p_pattern TEXT)
RETURNS TABLE(
    id INTEGER,
    name VARCHAR(100),
    phone VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.name, c.phone
    FROM contacts c
    WHERE c.name ILIKE '%' || p_pattern || '%'
       OR c.phone ILIKE '%' || p_pattern || '%'
    ORDER BY c.name;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_contacts_paginated(
    p_limit INTEGER,
    p_offset INTEGER
)
RETURNS TABLE(
    id INTEGER,
    name VARCHAR(100),
    phone VARCHAR(20),
    total_count BIGINT
) AS $$
DECLARE
    v_total BIGINT;
BEGIN

    SELECT COUNT(*) INTO v_total FROM contacts;
    
    RETURN QUERY
    SELECT c.id, c.name, c.phone, v_total
    FROM contacts c
    ORDER BY c.name
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION is_valid_phone(p_phone VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN

    RETURN p_phone ~ '^\+[0-9]{10,15}$';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_invalid_contacts()
RETURNS TABLE(
    name VARCHAR(100),
    phone VARCHAR(20),
    error_message TEXT
) AS $$
BEGIN

    CREATE TEMP TABLE IF NOT EXISTS temp_invalid_contacts (
        name VARCHAR(100),
        phone VARCHAR(20),
        error_message TEXT
    );
    
    RETURN QUERY
    SELECT t.name, t.phone, t.error_message
    FROM temp_invalid_contacts t;
    

    TRUNCATE temp_invalid_contacts;
END;
$$ LANGUAGE plpgsql;





CREATE OR REPLACE FUNCTION add_invalid_contact(
    p_name VARCHAR,
    p_phone VARCHAR,
    p_error TEXT
)
RETURNS VOID AS $$
BEGIN

    CREATE TEMP TABLE IF NOT EXISTS temp_invalid_contacts (
        name VARCHAR(100),
        phone VARCHAR(20),
        error_message TEXT
    );
    
    INSERT INTO temp_invalid_contacts (name, phone, error_message)
    VALUES (p_name, p_phone, p_error);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_contact_count()
RETURNS BIGINT AS $$
DECLARE
    v_count BIGINT;
BEGIN
    SELECT COUNT(*) INTO v_count FROM contacts;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;