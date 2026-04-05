-- Migration 007: Deadline provenance (program / scholarship extraction)
ALTER TABLE deadline_entries
  ADD COLUMN source_type ENUM('program', 'scholarship', 'manual', 'other') NOT NULL DEFAULT 'manual' AFTER checklist_id,
  ADD COLUMN source_id VARCHAR(128) NULL COMMENT 'External program or scholarship id' AFTER source_type;

CREATE INDEX idx_deadline_user_source ON deadline_entries (user_id, source_type, source_id);
