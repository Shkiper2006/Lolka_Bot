CREATE TABLE IF NOT EXISTS forms (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    created_by VARCHAR(128) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_forms_status ON forms(status);
