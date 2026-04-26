-- 1. Пагинация (беттеу) функциясы
CREATE OR REPLACE FUNCTION get_contacts_paginated(arg_limit INTEGER, arg_offset INTEGER)
RETURNS TABLE (
    id         INTEGER,
    first_name VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.first_name, c.email, c.birthday, g.name
    FROM contacts c
    LEFT JOIN groups g ON c.group_id = g.id
    ORDER BY c.id
    LIMIT arg_limit OFFSET arg_offset;
END;
$$ LANGUAGE plpgsql;

-- 2. Кеңейтілген іздеу функциясы (Python-дағы 11-ші пункт үшін)
CREATE OR REPLACE FUNCTION search_contacts(arg_query VARCHAR)
RETURNS TABLE (
    id         INTEGER,
    first_name VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR,
    phone      VARCHAR,
    phone_type VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.first_name, c.email, c.birthday, g.name, p.phone, p.type
    FROM contacts c
    LEFT JOIN groups g ON c.group_id = g.id
    LEFT JOIN phones p ON c.id = p.contact_id
    WHERE c.first_name ILIKE '%' || arg_query || '%'
       OR c.email      ILIKE '%' || arg_query || '%'
       OR p.phone      ILIKE '%' || arg_query || '%';
END;
$$ LANGUAGE plpgsql;

-- 3. Жаңа телефон қосу процедурасы
CREATE OR REPLACE PROCEDURE add_phone(
    arg_name  VARCHAR,
    arg_phone VARCHAR,
    arg_type  VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    found_contact_id INTEGER;
BEGIN
    SELECT id INTO found_contact_id FROM contacts WHERE first_name = arg_name;

    IF found_contact_id IS NOT NULL THEN
        INSERT INTO phones (contact_id, phone, type)
        VALUES (found_contact_id, arg_phone, arg_type);
    ELSE
        RAISE EXCEPTION 'Контакт % табылмады!', arg_name;
    END IF;
END;
$$;
