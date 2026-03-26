-- Migration 004: Deadline Entries (Separate table for querying)
CREATE TABLE IF NOT EXISTS deadline_entries (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID v4',
    user_id VARCHAR(36) NOT NULL,
    checklist_id VARCHAR(36) NULL COMMENT 'Related checklist if applicable',

    -- Deadline details
    deadline_date DATE NOT NULL,
    deadline_time TIME NULL,
    item_description VARCHAR(500) NOT NULL,
    item_category ENUM('application', 'document', 'test', 'interview', 'other') DEFAULT 'application',
    priority ENUM('high', 'medium', 'low') DEFAULT 'medium',

    -- Status
    status ENUM('pending', 'completed', 'missed') DEFAULT 'pending',
    reminder_sent BOOLEAN DEFAULT FALSE,
    reminder_sent_at TIMESTAMP NULL,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_checklist_id (checklist_id),
    INDEX idx_deadline_date (deadline_date),
    INDEX idx_status (status),
    INDEX idx_reminder (reminder_sent, deadline_date),

    FOREIGN KEY (checklist_id) REFERENCES application_checklists(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
