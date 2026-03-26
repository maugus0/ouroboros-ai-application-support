-- Migration 003: Application Checklists
CREATE TABLE IF NOT EXISTS application_checklists (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID v4',
    user_id VARCHAR(36) NOT NULL,
    program_id VARCHAR(36) NULL COMMENT 'Target program if applicable',

    -- Checklist content (JSON)
    items JSON NOT NULL COMMENT 'Array of {id, description, status, category, priority}',
    overall_status ENUM('not_started', 'in_progress', 'completed') DEFAULT 'not_started',
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_program_id (program_id),
    INDEX idx_status (overall_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
