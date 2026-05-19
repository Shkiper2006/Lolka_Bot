INSERT INTO forms (id, title, description, status, created_by)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Тестовая анкета',
    'Seed-форма для ручной проверки submit-потока',
    'published',
    'seed-script'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO form_fields (id, form_id, label, type, required, options, field_order, validation_rules)
VALUES
    (
        '22222222-2222-2222-2222-222222222221',
        '11111111-1111-1111-1111-111111111111',
        'Ваше имя',
        'short_text',
        TRUE,
        '[]'::jsonb,
        1,
        '{"min_length": 2}'::jsonb
    ),
    (
        '22222222-2222-2222-2222-222222222222',
        '11111111-1111-1111-1111-111111111111',
        'Выберите тариф',
        'select',
        TRUE,
        '["basic", "pro", "enterprise"]'::jsonb,
        2,
        '{}'::jsonb
    )
ON CONFLICT (id) DO NOTHING;
