CREATE TABLE IF NOT EXISTS submission_answers (
    id VARCHAR(36) PRIMARY KEY,
    submission_id VARCHAR(36) NOT NULL REFERENCES form_submissions(id) ON DELETE CASCADE,
    field_id VARCHAR(36) NOT NULL REFERENCES form_fields(id) ON DELETE CASCADE,
    answer_value JSONB
);
