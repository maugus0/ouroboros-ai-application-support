-- Migration 008: Ensure match_attribution_snapshot exists on generated_sops.
-- Idempotent: no-op when column already present (e.g. fresh installs from 001).
-- Use when an older database ran 001 before that column was added to the schema.
SET @db = DATABASE();
SET @exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'generated_sops'
    AND COLUMN_NAME = 'match_attribution_snapshot'
);
SET @query = IF(
  @exists > 0,
  'DO 1',
  'ALTER TABLE generated_sops ADD COLUMN match_attribution_snapshot JSON NULL COMMENT ''Match scoring / attribution payload at generation time'' AFTER retrieved_reference_ids'
);
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
