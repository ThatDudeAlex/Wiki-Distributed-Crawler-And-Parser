/**************************************************
 * ENUM TYPES
 **************************************************/

-- Create ENUM type only if it doesn't exist
-- NOTE: PostgreSQL does not support `CREATE TYPE IF NOT EXISTS`, so we simulate it
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'crawl_status_enum'
    ) THEN
        CREATE TYPE crawl_status_enum AS ENUM (
            'PENDING',
            'CRAWLED_SUCCESS',
            'CRAWL_FAILED',
            'SKIPPED'
        );
    END IF;
END
$$;


/**************************************************
 * FUNCTIONS
 **************************************************/

-- Function that updates the `updated_at` column to the current timestamp
CREATE OR REPLACE FUNCTION set_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


/**************************************************
 * TABLE: pages
 **************************************************/

CREATE TABLE IF NOT EXISTS pages (
    page_id             BIGSERIAL PRIMARY KEY,
    url                 VARCHAR(2048) UNIQUE NOT NULL,
    title               VARCHAR(512),
    last_crawled_at     TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    next_crawl_at       TIMESTAMPTZ,
    last_crawl_status   crawl_status_enum NOT NULL DEFAULT 'PENDING',
    http_status_code    INTEGER,
    crawl_attempts      INTEGER DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for `pages` table
CREATE INDEX IF NOT EXISTS idx_pages_url             ON pages (url);
CREATE INDEX IF NOT EXISTS idx_pages_title           ON pages (title);
CREATE INDEX IF NOT EXISTS dx__last_crawled          ON pages (last_crawled_at);
CREATE INDEX IF NOT EXISTS idx_next_crawl            ON pages (next_crawl_at);
CREATE INDEX IF NOT EXISTS idx_last_crawl_status     ON pages (last_crawl_status);


/****
 * TRIGGERS: pages
 ****/

-- Drop trigger if it already exists
DROP TRIGGER IF EXISTS update_pages_updated_at ON pages;

-- Create trigger to auto-update `updated_at` on row update
CREATE TRIGGER update_pages_updated_at
BEFORE UPDATE ON pages
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_timestamp();


/**************************************************
 * TABLE: links
 **************************************************/

CREATE TABLE IF NOT EXISTS links (
    source_page_id  BIGINT NOT NULL,
    target_url      VARCHAR(2048) NOT NULL,
    link_text       VARCHAR(512),
    is_internal     BOOLEAN NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_page_id, target_url),
    CONSTRAINT fk_source_page
        FOREIGN KEY (source_page_id)
        REFERENCES pages (page_id)
        ON DELETE CASCADE
);

-- Indexes for `links` table
CREATE INDEX IF NOT EXISTS idx_source_page_id ON links (source_page_id);
