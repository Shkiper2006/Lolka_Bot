CREATE TABLE IF NOT EXISTS form_submissions (
    id VARCHAR(36) PRIMARY KEY,
    form_id VARCHAR(36) NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
    user_id VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_form_submissions_form_user_created
    ON form_submissions(form_id, user_id, created_at);
