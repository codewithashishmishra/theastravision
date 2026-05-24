ATTACH TABLE _ UUID '54b2159d-ede9-4867-9648-426910b44d0c'
(
    `id` UUID,
    `log_type` LowCardinality(String),
    `tenant_id` UUID,
    `tenant_name` Nullable(String),
    `user_id` Nullable(UUID),
    `user_email` Nullable(String),
    `module` String,
    `action` String,
    `level` LowCardinality(String),
    `service` LowCardinality(String),
    `message` String,
    `ip_address` Nullable(String),
    `metadata` String,
    `created_at` DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(created_at)
ORDER BY (log_type, tenant_id, created_at)
SETTINGS index_granularity = 8192
