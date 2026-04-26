-- Тапсырыс берушілер (Топтар) кестесі
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL       PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Контактілер кестесі
CREATE TABLE IF NOT EXISTS contacts (
    id         SERIAL       PRIMARY KEY,
    group_id   INTEGER      REFERENCES groups(id),
    first_name VARCHAR(100) NOT NULL,
    email      VARCHAR(255),
    birthday   DATE,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- Телефондар кестесі (Бір контактіде бірнеше нөмір болуы үшін)
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL      PRIMARY KEY,
    contact_id INTEGER     REFERENCES contacts(id) ON DELETE CASCADE,
    type       VARCHAR(20) DEFAULT 'mobile', -- home, work, mobile
    phone      VARCHAR(20) NOT NULL
);
