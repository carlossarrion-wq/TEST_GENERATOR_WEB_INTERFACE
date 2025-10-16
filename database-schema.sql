-- =======================================================
-- Test Plan Generator - Database Schema
-- RDS MySQL 8.0 Schema Creation Script
-- =======================================================

-- Use the database
USE testplangenerator;

-- =======================================================
-- Table: auth_users
-- Authentication users with AWS-style Access Key/Secret Key
-- =======================================================
CREATE TABLE auth_users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    access_key VARCHAR(128) UNIQUE NOT NULL,      -- AWS-style access key (e.g., AKIA...)
    secret_key_hash VARCHAR(256) NOT NULL,        -- SHA-256 hash of secret key
    permissions JSON DEFAULT NULL,                -- User permissions array
    is_active BOOLEAN DEFAULT TRUE,               -- Account status
    last_login_at TIMESTAMP NULL,                 -- Last successful login
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Indexes for performance
    INDEX idx_access_key (access_key),
    INDEX idx_is_active (is_active),
    INDEX idx_is_deleted (is_deleted),
    INDEX idx_last_login (last_login_at)
);

-- =======================================================
-- Table: auth_sessions
-- Active authentication sessions
-- =======================================================
CREATE TABLE auth_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,                      -- Foreign key to auth_users
    session_token TEXT NOT NULL,                  -- Encrypted session token
    expires_at TIMESTAMP NOT NULL,                -- Session expiration time
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    
    -- Indexes for performance
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_session_token (session_token(255)),  -- Index first 255 chars of token
    
    -- Unique constraint to ensure one active session per user
    UNIQUE KEY unique_user_session (user_id)
);

-- =======================================================
-- Table: test_plans
-- Main table for storing test plans
-- =======================================================
CREATE TABLE test_plans (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plan_id VARCHAR(50) UNIQUE NOT NULL,           -- Unique identifier like TP-timestamp-random
    title VARCHAR(500) NOT NULL,                   -- Test plan title
    reference VARCHAR(100),                        -- Jira or external reference
    requirements TEXT,                             -- Test requirements description
    coverage_percentage TINYINT DEFAULT 80,       -- Target coverage percentage (10-100)
    min_test_cases TINYINT DEFAULT 5,             -- Minimum number of test cases
    max_test_cases TINYINT DEFAULT 15,            -- Maximum number of test cases
    selected_test_types JSON,                      -- Array of test types ["unit", "integration", etc.]
    status ENUM('draft', 'active', 'completed', 'archived') DEFAULT 'draft',
    created_by_user_id BIGINT,                    -- User who created this plan
    modified_by_user_id BIGINT,                   -- User who last modified this plan
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Foreign key constraints
    FOREIGN KEY (created_by_user_id) REFERENCES auth_users(id) ON DELETE SET NULL,
    FOREIGN KEY (modified_by_user_id) REFERENCES auth_users(id) ON DELETE SET NULL,
    
    -- Indexes for performance
    INDEX idx_plan_id (plan_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_is_deleted (is_deleted),
    INDEX idx_created_by (created_by_user_id),
    INDEX idx_modified_by (modified_by_user_id)
);

-- =======================================================
-- Table: test_cases
-- Individual test cases belonging to test plans
-- =======================================================
CREATE TABLE test_cases (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    test_plan_id BIGINT NOT NULL,                  -- Foreign key to test_plans
    case_id VARCHAR(20) NOT NULL,                  -- Case identifier like TC-001, TC-002
    name VARCHAR(500) NOT NULL,                    -- Test case name
    description TEXT,                              -- Detailed description
    priority ENUM('High', 'Medium', 'Low') DEFAULT 'Medium',
    preconditions TEXT,                            -- Prerequisites for the test
    expected_result TEXT,                          -- Expected outcome
    test_data TEXT,                               -- Test data or parameters
    case_order SMALLINT DEFAULT 0,               -- Order within the test plan
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Foreign key constraint
    FOREIGN KEY (test_plan_id) REFERENCES test_plans(id) ON DELETE CASCADE,
    
    -- Indexes for performance
    INDEX idx_test_plan_id (test_plan_id),
    INDEX idx_case_id (case_id),
    INDEX idx_priority (priority),
    INDEX idx_case_order (case_order),
    INDEX idx_is_deleted (is_deleted),
    
    -- Composite index for common queries
    INDEX idx_plan_order (test_plan_id, case_order)
);

-- =======================================================
-- Table: test_steps
-- Individual steps within test cases
-- =======================================================
CREATE TABLE test_steps (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    test_case_id BIGINT NOT NULL,                  -- Foreign key to test_cases
    step_number TINYINT NOT NULL,                  -- Step number (1, 2, 3, etc.)
    description TEXT NOT NULL,                     -- Step description/action
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE,
    
    -- Indexes for performance
    INDEX idx_test_case_id (test_case_id),
    INDEX idx_step_number (step_number),
    
    -- Composite index for ordered retrieval
    INDEX idx_case_step (test_case_id, step_number),
    
    -- Unique constraint to prevent duplicate step numbers within a test case
    UNIQUE KEY unique_case_step (test_case_id, step_number)
);

-- =======================================================
-- Table: chat_messages
-- Chat history for test plans
-- =======================================================
CREATE TABLE chat_messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    test_plan_id BIGINT NOT NULL,                  -- Foreign key to test_plans
    message_type ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,                         -- Message content
    message_order SMALLINT NOT NULL,              -- Order of messages in conversation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (test_plan_id) REFERENCES test_plans(id) ON DELETE CASCADE,
    
    -- Indexes for performance
    INDEX idx_test_plan_id (test_plan_id),
    INDEX idx_message_type (message_type),
    INDEX idx_created_at (created_at),
    
    -- Composite index for ordered retrieval
    INDEX idx_plan_order (test_plan_id, message_order),
    
    -- Unique constraint to prevent duplicate message orders within a test plan
    UNIQUE KEY unique_plan_message_order (test_plan_id, message_order)
);

-- =======================================================
-- Sample Data for Testing
-- =======================================================

-- Insert a sample test plan
INSERT INTO test_plans (
    plan_id, title, reference, requirements, coverage_percentage, 
    min_test_cases, max_test_cases, selected_test_types, status
) VALUES (
    'TP-1699123456789-0001',
    'User Authentication Test Plan',
    'JIRA-1234',
    'Users must be able to log in securely using username and password. The system should validate credentials and provide appropriate feedback for success and failure scenarios.',
    80,
    5,
    15,
    '["unit", "integration", "security"]',
    'draft'
);

-- Get the inserted test plan ID
SET @test_plan_id = LAST_INSERT_ID();

-- Insert sample test cases
INSERT INTO test_cases (
    test_plan_id, case_id, name, description, priority, 
    preconditions, expected_result, test_data, case_order
) VALUES
(
    @test_plan_id,
    'TC-001',
    'Test login with valid credentials',
    'Verify that a user can successfully log in with valid username and password',
    'High',
    'User account exists in the system and is active',
    'User is logged in successfully and redirected to dashboard',
    'Username: testuser@example.com, Password: ValidPass123!',
    1
),
(
    @test_plan_id,
    'TC-002',
    'Test login with invalid password',
    'Verify that login fails with incorrect password',
    'High',
    'User account exists in the system',
    'Login fails with appropriate error message',
    'Username: testuser@example.com, Password: WrongPassword',
    2
),
(
    @test_plan_id,
    'TC-003',
    'Test login with non-existent user',
    'Verify that login fails for non-existent user account',
    'Medium',
    'User account does not exist in the system',
    'Login fails with appropriate error message',
    'Username: nonexistent@example.com, Password: AnyPassword123',
    3
);

-- Insert sample test steps for TC-001
INSERT INTO test_steps (test_case_id, step_number, description) VALUES
((SELECT id FROM test_cases WHERE case_id = 'TC-001' AND test_plan_id = @test_plan_id), 1, 'Navigate to the login page'),
((SELECT id FROM test_cases WHERE case_id = 'TC-001' AND test_plan_id = @test_plan_id), 2, 'Enter valid username in the username field'),
((SELECT id FROM test_cases WHERE case_id = 'TC-001' AND test_plan_id = @test_plan_id), 3, 'Enter valid password in the password field'),
((SELECT id FROM test_cases WHERE case_id = 'TC-001' AND test_plan_id = @test_plan_id), 4, 'Click the Login button'),
((SELECT id FROM test_cases WHERE case_id = 'TC-001' AND test_plan_id = @test_plan_id), 5, 'Verify successful login and dashboard access');

-- Insert sample test steps for TC-002
INSERT INTO test_steps (test_case_id, step_number, description) VALUES
((SELECT id FROM test_cases WHERE case_id = 'TC-002' AND test_plan_id = @test_plan_id), 1, 'Navigate to the login page'),
((SELECT id FROM test_cases WHERE case_id = 'TC-002' AND test_plan_id = @test_plan_id), 2, 'Enter valid username in the username field'),
((SELECT id FROM test_cases WHERE case_id = 'TC-002' AND test_plan_id = @test_plan_id), 3, 'Enter invalid password in the password field'),
((SELECT id FROM test_cases WHERE case_id = 'TC-002' AND test_plan_id = @test_plan_id), 4, 'Click the Login button'),
((SELECT id FROM test_cases WHERE case_id = 'TC-002' AND test_plan_id = @test_plan_id), 5, 'Verify error message is displayed');

-- Insert sample chat messages
INSERT INTO chat_messages (test_plan_id, message_type, content, message_order) VALUES
(@test_plan_id, 'user', 'Generate test cases for user authentication', 1),
(@test_plan_id, 'assistant', 'I can help you create comprehensive test cases for user authentication. Based on your requirements, I will generate test cases covering valid login, invalid credentials, and edge cases.', 2),
(@test_plan_id, 'user', 'Add security test cases', 3),
(@test_plan_id, 'assistant', 'I will add security-focused test cases including SQL injection attempts, brute force protection, and session management tests.', 4);

-- =======================================================
-- Utility Views for Common Queries
-- =======================================================

-- View for complete test plan with case counts
CREATE VIEW test_plans_summary AS
SELECT 
    tp.id,
    tp.plan_id,
    tp.title,
    tp.reference,
    tp.status,
    tp.coverage_percentage,
    COUNT(tc.id) as test_cases_count,
    tp.created_at,
    tp.updated_at
FROM test_plans tp
LEFT JOIN test_cases tc ON tp.id = tc.test_plan_id AND tc.is_deleted = FALSE
WHERE tp.is_deleted = FALSE
GROUP BY tp.id, tp.plan_id, tp.title, tp.reference, tp.status, tp.coverage_percentage, tp.created_at, tp.updated_at;

-- View for test cases with step counts
CREATE VIEW test_cases_summary AS
SELECT 
    tc.id,
    tc.test_plan_id,
    tc.case_id,
    tc.name,
    tc.priority,
    tc.case_order,
    COUNT(ts.id) as steps_count,
    tc.created_at,
    tc.updated_at
FROM test_cases tc
LEFT JOIN test_steps ts ON tc.id = ts.test_case_id
WHERE tc.is_deleted = FALSE
GROUP BY tc.id, tc.test_plan_id, tc.case_id, tc.name, tc.priority, tc.case_order, tc.created_at, tc.updated_at
ORDER BY tc.case_order;

-- =======================================================
-- Performance Optimization
-- =======================================================

-- Additional indexes for common query patterns
CREATE INDEX idx_test_plans_title_search ON test_plans(title(255));
CREATE INDEX idx_test_plans_requirements_search ON test_plans(requirements(255));
CREATE INDEX idx_test_cases_name_search ON test_cases(name(255));

-- =======================================================
-- Database Statistics and Information
-- =======================================================

-- Show table information
SELECT 
    'Database schema created successfully!' as message,
    NOW() as created_at;

-- Show table counts
SELECT 
    'test_plans' as table_name,
    COUNT(*) as record_count
FROM test_plans
UNION ALL
SELECT 
    'test_cases' as table_name,
    COUNT(*) as record_count
FROM test_cases
UNION ALL
SELECT 
    'test_steps' as table_name,
    COUNT(*) as record_count
FROM test_steps
UNION ALL
SELECT 
    'chat_messages' as table_name,
    COUNT(*) as record_count
FROM chat_messages;
