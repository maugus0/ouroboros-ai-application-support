-- Migration 007: Deadline provenance (program / scholarship extraction)
SET @db = DATABASE();

SET @exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'deadline_entries'
    AND COLUMN_NAME = 'source_type'
);
SET @query = IF(
  @exists > 0,
  'DO 1',
  'ALTER TABLE deadline_entries ADD COLUMN source_type ENUM(''program'', ''scholarship'', ''manual'', ''other'') NOT NULL DEFAULT ''manual'' AFTER checklist_id'
);
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @exists = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'deadline_entries'
    AND COLUMN_NAME = 'source_id'
);
SET @query = IF(
  @exists > 0,
  'DO 1',
  'ALTER TABLE deadline_entries ADD COLUMN source_id VARCHAR(128) NULL COMMENT ''External program or scholarship id'' AFTER source_type'
);
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @exists = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @db
    AND TABLE_NAME = 'deadline_entries'
    AND INDEX_NAME = 'idx_deadline_user_source'
);
SET @query = IF(
  @exists > 0,
  'DO 1',
  'CREATE INDEX idx_deadline_user_source ON deadline_entries (user_id, source_type, source_id)'
);
PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
