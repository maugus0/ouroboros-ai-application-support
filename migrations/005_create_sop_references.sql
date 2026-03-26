-- Migration 005: SOP References (for retrieval-assisted style guidance)
CREATE TABLE IF NOT EXISTS sop_references (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID v4',

    -- Content
    content TEXT NOT NULL,
    word_count INT NOT NULL,

    -- Metadata for filtering
    field_of_study VARCHAR(100) NULL COMMENT 'e.g., Computer Science, Biology',
    degree_level ENUM('bachelor', 'master', 'phd') NULL,
    program_type ENUM('research', 'coursework', 'professional') NULL,
    university_tier ENUM('tier1', 'tier2', 'tier3') NULL COMMENT 'Optional: T10, T50, T100+',

    -- Quality indicators
    quality_rating ENUM('excellent', 'good', 'average') DEFAULT 'good',
    notes TEXT NULL COMMENT 'Why this is a good example',

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_field_degree (field_of_study, degree_level),
    INDEX idx_program_type (program_type),
    INDEX idx_quality (quality_rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
