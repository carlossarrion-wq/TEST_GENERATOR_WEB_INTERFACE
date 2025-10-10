#!/usr/bin/env python3
"""
Fix MySQL authentication plugin for Lambda
"""

import pymysql
import sys

# Database connection parameters
DB_CONFIG = {
    'host': 'test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'TempPassword123!',
    'database': 'testplangenerator',
    'port': 3306,
    'charset': 'utf8mb4',
    'connect_timeout': 60
}

def fix_auth():
    """Fix authentication plugin for Lambda users"""
    try:
        print("🔄 Connecting to database...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("✅ Connected successfully!")
        
        # Check authentication plugins
        print("\n📋 Current authentication plugins:")
        cursor.execute("""
            SELECT user, host, plugin 
            FROM mysql.user 
            WHERE user='admin';
        """)
        users = cursor.fetchall()
        for user in users:
            print(f"   - User: {user[0]}, Host: {user[1]}, Plugin: {user[2]}")
        
        print("\n🔄 Dropping and recreating users with mysql_native_password...")
        
        # Drop existing users and recreate with correct plugin
        patterns = ['10.0.2.93', '10.0.2.%', '10.0.%', '10.%']
        
        for pattern in patterns:
            try:
                # Drop user if exists
                cursor.execute(f"DROP USER IF EXISTS 'admin'@'{pattern}';")
                print(f"✅ Dropped 'admin'@'{pattern}'")
                
                # Create with mysql_native_password
                cursor.execute(f"""
                    CREATE USER 'admin'@'{pattern}' 
                    IDENTIFIED WITH mysql_native_password 
                    BY 'TempPassword123!';
                """)
                print(f"✅ Created 'admin'@'{pattern}' with mysql_native_password")
                
                # Grant privileges
                cursor.execute(f"""
                    GRANT ALL PRIVILEGES ON testplangenerator.* 
                    TO 'admin'@'{pattern}';
                """)
                print(f"✅ Granted privileges to 'admin'@'{pattern}'")
                
            except Exception as e:
                print(f"⚠️  Pattern {pattern}: {e}")
        
        # Flush privileges
        cursor.execute("FLUSH PRIVILEGES;")
        print("\n✅ Privileges flushed")
        
        # Verify authentication plugins again
        print("\n📋 Updated authentication plugins:")
        cursor.execute("""
            SELECT user, host, plugin 
            FROM mysql.user 
            WHERE user='admin';
        """)
        users = cursor.fetchall()
        for user in users:
            print(f"   - User: {user[0]}, Host: {user[1]}, Plugin: {user[2]}")
        
        # Test query
        print("\n🧪 Testing query...")
        cursor.execute("SELECT COUNT(*) FROM test_plans;")
        count = cursor.fetchone()[0]
        print(f"✅ Query successful: {count} test plans")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 Authentication fixed successfully!")
        print("\n⚠️  IMPORTANTE: Espera 30-60 segundos para que Lambda recoja los cambios")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_auth()
    sys.exit(0 if success else 1)
