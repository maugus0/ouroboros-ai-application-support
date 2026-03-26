-- Migration 002: Generated Cover Letters
CREATE TABLE IF NOT EXISTS generated_cover_letters (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID v4',
    user_id VARCHAR(36) NOT NULL,
    target_type ENUM('program', 'scholarship', 'professor', 'other') NOT NULL,
    target_id VARCHAR(36) NULL COMMENT 'Program/scholarship ID if applicable',

    -- Version control
    version INT NOT NULL DEFAULT 1,
    parent_letter_id VARCHAR(36) NULL,

    -- Content
    content TEXT NOT NULL,
    word_count INT NOT NULL,

    -- Metadata
    llm_model_used VARCHAR(100) NULL,
    llm_fallback_used BOOLEAN DEFAULT FALSE,
    total_processing_time_ms INT NULL,
    prompt_version VARCHAR(50) NULL,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_target (target_type, target_id),
    INDEX idx_parent_letter (parent_letter_id),

    FOREIGN KEY (parent_letter_id) REFERENCES generated_cover_letters(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
