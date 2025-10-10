#!/usr/bin/env python3
"""
Fix MySQL user permissions for specific Lambda IP
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
    """Fix user permissions for Lambda IP 10.0.2.93"""
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
        
        print("\n🔄 Creating user for specific Lambda IP...")
        
        # Create user for specific IP
        try:
            cursor.execute("""
                CREATE USER IF NOT EXISTS 'admin'@'10.0.2.93' 
                IDENTIFIED BY 'TempPassword123!';
            """)
            print("✅ User 'admin'@'10.0.2.93' created")
        except Exception as e:
            print(f"⚠️  User creation: {e}")
        
        # Grant all privileges
        cursor.execute("""
            GRANT ALL PRIVILEGES ON testplangenerator.* 
            TO 'admin'@'10.0.2.93';
        """)
        print("✅ Granted privileges to 'admin'@'10.0.2.93'")
        
        # Also try with broader subnet patterns
        for pattern in ['10.0.2.%', '10.%']:
            try:
                cursor.execute(f"""
                    CREATE USER IF NOT EXISTS 'admin'@'{pattern}' 
                    IDENTIFIED BY 'TempPassword123!';
                """)
                cursor.execute(f"""
                    GRANT ALL PRIVILEGES ON testplangenerator.* 
                    TO 'admin'@'{pattern}';
                """)
                print(f"✅ User 'admin'@'{pattern}' configured")
            except Exception as e:
                print(f"⚠️  Pattern {pattern}: {e}")
        
        # Flush privileges
        cursor.execute("FLUSH PRIVILEGES;")
        print("✅ Privileges flushed")
        
        # Verify permissions
        print("\n📋 Updated admin users:")
        cursor.execute("SELECT user, host FROM mysql.user WHERE user='admin';")
        users = cursor.fetchall()
        for user in users:
            print(f"   - User: {user[0]}, Host: {user[1]}")
        
        # Show grants for specific IP
        print("\n🔍 Grants for 'admin'@'10.0.2.93':")
        try:
            cursor.execute("SHOW GRANTS FOR 'admin'@'10.0.2.93';")
            grants = cursor.fetchall()
            for grant in grants:
                print(f"   {grant[0]}")
        except Exception as e:
            print(f"   ⚠️  {e}")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 Permissions fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_permissions()
    sys.exit(0 if success else 1)
