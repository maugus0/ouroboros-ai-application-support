-- Migration 001: Generated SOPs with versioning
CREATE TABLE IF NOT EXISTS generated_sops (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID v4',
    user_id VARCHAR(36) NOT NULL,
    program_id VARCHAR(36) NULL COMMENT 'Target program if applicable',

    -- Version control
    version INT NOT NULL DEFAULT 1,
    parent_sop_id VARCHAR(36) NULL COMMENT 'Previous version if refinement',

    -- Content
    content TEXT NOT NULL,
    word_count INT NOT NULL,

    -- Quality metadata
    quality_score DECIMAL(3,2) NULL COMMENT '0.00-1.00',
    quality_feedback JSON NULL COMMENT 'LLM suggestions for improvement',

    -- Pipeline metadata
    outline JSON NULL COMMENT 'Step 1 output',
    expanded_content TEXT NULL COMMENT 'Step 2 output before review',
    llm_model_used VARCHAR(100) NULL,
    llm_fallback_used BOOLEAN DEFAULT FALSE,
    total_processing_time_ms INT NULL,
    prompt_version VARCHAR(50) NULL COMMENT 'e.g., sop_v1',

    -- Retrieval metadata
    retrieved_reference_ids JSON NULL COMMENT 'Array of SOP reference IDs used for style',
    match_attribution_snapshot JSON NULL COMMENT 'Match scoring / attribution payload at generation time (eligibility or orchestrator)',

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_program_id (program_id),
    INDEX idx_parent_sop (parent_sop_id),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (parent_sop_id) REFERENCES generated_sops(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
