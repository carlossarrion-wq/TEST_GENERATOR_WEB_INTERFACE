-- Tabla para almacenar el estado de las tareas asíncronas
-- Esto permite bypass del timeout de API Gateway (29 segundos)

CREATE TABLE IF NOT EXISTS async_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(36) UNIQUE NOT NULL,
    status ENUM('processing', 'completed', 'failed') NOT NULL DEFAULT 'processing',
    request_data TEXT,
    result_data LONGTEXT,
    error_message TEXT,
    message VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Agregar comentarios para documentación
ALTER TABLE async_tasks 
