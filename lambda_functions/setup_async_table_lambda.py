"""
Lambda function temporal para crear la tabla async_tasks
Se ejecuta una vez y luego se puede eliminar
"""

import json
import pymysql

DB_CONFIG = {
    'host': 'test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'TempPassword123!',
    'database': 'testplangenerator',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

SQL_CREATE_TABLE = """
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
"""

def lambda_handler(event, context):
    """Handler para crear la tabla async_tasks"""
    try:
        print("🔌 Conectando a MySQL RDS desde Lambda...")
        connection = pymysql.connect(**DB_CONFIG)
        
        print("✅ Conexión exitosa")
        
        with connection.cursor() as cursor:
            print("📝 Creando tabla async_tasks...")
            cursor.execute(SQL_CREATE_TABLE)
            connection.commit()
            
            print("✅ Tabla creada")
            
            # Verificar
            cursor.execute("SHOW TABLES LIKE 'async_tasks'")
            result = cursor.fetchone()
            
            if result:
                cursor.execute("DESCRIBE async_tasks")
                columns = cursor.fetchall()
                
                column_info = [f"{col['Field']}: {col['Type']}" for col in columns]
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': 'Tabla async_tasks creada exitosamente',
                        'columns': column_info
                    })
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'No se pudo verificar la tabla'})
                }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    finally:
        if 'connection' in locals():
            connection.close()
