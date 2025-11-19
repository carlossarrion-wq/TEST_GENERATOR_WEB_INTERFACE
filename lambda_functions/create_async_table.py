#!/usr/bin/env python3
"""
Script para crear la tabla async_tasks en MySQL RDS
Usa las mismas credenciales que db_utils.py
"""

import pymysql
import sys

# Configuración de la base de datos (misma que db_utils.py)
DB_CONFIG = {
    'host': 'test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Admin123',  # Asegúrate de que esta sea la contraseña correcta
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

def create_table():
    """Crear la tabla async_tasks"""
    try:
        print("🔌 Conectando a MySQL RDS...")
        connection = pymysql.connect(**DB_CONFIG)
        
        print("✅ Conexión exitosa")
        print(f"📊 Base de datos: {DB_CONFIG['database']}")
        print(f"🖥️  Host: {DB_CONFIG['host']}")
        
        with connection.cursor() as cursor:
            print("\n📝 Ejecutando SQL para crear tabla async_tasks...")
            cursor.execute(SQL_CREATE_TABLE)
            connection.commit()
            
            print("✅ Tabla async_tasks creada exitosamente")
            
            # Verificar que la tabla existe
            cursor.execute("SHOW TABLES LIKE 'async_tasks'")
            result = cursor.fetchone()
            
            if result:
                print("\n🔍 Verificando estructura de la tabla...")
                cursor.execute("DESCRIBE async_tasks")
                columns = cursor.fetchall()
                
                print("\n📋 Columnas de la tabla async_tasks:")
                for col in columns:
                    print(f"   - {col['Field']}: {col['Type']}")
                
                print("\n✨ ¡Todo listo! La tabla async_tasks está creada y lista para usar.")
            else:
                print("⚠️  Advertencia: No se pudo verificar la tabla")
        
        connection.close()
        return True
        
    except pymysql.Error as e:
        print(f"\n❌ Error de MySQL: {e}")
        print(f"   Código de error: {e.args[0]}")
        print(f"   Mensaje: {e.args[1]}")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  Creación de Tabla async_tasks en MySQL RDS")
    print("=" * 60)
    print()
    
    success = create_table()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        sys.exit(0)
    else:
        print("❌ PROCESO FALLÓ - Revisa los errores arriba")
        sys.exit(1)
