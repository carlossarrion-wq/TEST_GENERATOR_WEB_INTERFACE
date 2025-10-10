#!/usr/bin/env python3
"""
Fix MySQL user permissions for Lambda access
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

def fix_permissions():
    """Fix user permissions to allow connections from VPC"""
    try:
        print("🔄 Connecting to database...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("✅ Connected successfully!")
        
        # Check current users
        print("\n📋 Current admin users:")
        cursor.execute("SELECT user, host FROM mysql.user WHERE user='admin';")
        users = cursor.fetchall()
        for user in users:
            print(f"   - User: {user[0]}, Host: {user[1]}")
        
        # Grant permissions from VPC subnet (10.0.0.0/16)
        print("\n🔄 Granting permissions for VPC access...")
        
        # Create user for VPC subnet if not exists
        try:
            cursor.execute("""
                CREATE USER IF NOT EXISTS 'admin'@'10.0.%' 
                IDENTIFIED BY 'TempPassword123!';
            """)
            print("✅ User 'admin'@'10.0.%' created/verified")
        except Exception as e:
            print(f"⚠️  User creation: {e}")
        
        # Grant all privileges
        cursor.execute("""
            GRANT ALL PRIVILEGES ON testplangenerator.* 
            TO 'admin'@'10.0.%';
        """)
        print("✅ Granted privileges to 'admin'@'10.0.%'")
        
        # Also ensure % wildcard has permissions
        try:
            cursor.execute("""
                CREATE USER IF NOT EXISTS 'admin'@'%' 
                IDENTIFIED BY 'TempPassword123!';
            """)
            print("✅ User 'admin'@'%' created/verified")
        except Exception as e:
            print(f"⚠️  User creation: {e}")
        
        cursor.execute("""
            GRANT ALL PRIVILEGES ON testplangenerator.* 
            TO 'admin'@'%';
        """)
        print("✅ Granted privileges to 'admin'@'%'")
        
        # Flush privileges
        cursor.execute("FLUSH PRIVILEGES;")
        print("✅ Privileges flushed")
        
        # Verify permissions
        print("\n📋 Updated admin users:")
        cursor.execute("SELECT user, host FROM mysql.user WHERE user='admin';")
        users = cursor.fetchall()
        for user in users:
            print(f"   - User: {user[0]}, Host: {user[1]}")
        
        # Test connection from Lambda perspective
        print("\n🧪 Testing permissions...")
        cursor.execute("SELECT COUNT(*) FROM test_plans;")
        count = cursor.fetchone()[0]
        print(f"✅ Can query test_plans table: {count} records")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 Permissions fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_permissions()
    sys.exit(0 if success else 1)
