#!/usr/bin/env python3
"""
Database Setup Script for Test Plan Generator
Executes the database schema creation on RDS MySQL
"""

import pymysql
import time
import sys

# Database connection parameters
DB_CONFIG = {
    'host': 'test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'TempPassword123!',
    'database': 'testplangenerator',
    'port': 3306,
    'charset': 'utf8mb4',
    'connect_timeout': 60,
    'read_timeout': 60,
    'write_timeout': 60,
    'autocommit': True
}

def test_connection():
    """Test database connection"""
    try:
        print("🔄 Testing database connection...")
        connection = pymysql.connect(**DB_CONFIG)
        print("✅ Database connection successful!")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def execute_schema():
    """Execute the database schema from file"""
    try:
        print("🔄 Reading database schema file...")
        with open('database-schema.sql', 'r', encoding='utf-8') as file:
            schema_sql = file.read()
        
        print("🔄 Connecting to database...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        print("🔄 Executing database schema...")
        
        # Split SQL commands (handle multi-statement execution)
        statements = []
        current_statement = ""
        
        for line in schema_sql.split('\n'):
            # Skip comments and empty lines
            line = line.strip()
            if not line or line.startswith('--'):
                continue
                
            current_statement += line + '\n'
            
            # Check if statement is complete (ends with semicolon)
            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Execute each statement
        executed_count = 0
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                try:
                    cursor.execute(statement)
                    executed_count += 1
                    print(f"✅ Executed statement {i}/{len(statements)}")
                except Exception as e:
                    print(f"⚠️  Warning on statement {i}: {e}")
                    # Continue with other statements
        
        print(f"🎉 Schema execution completed! {executed_count} statements executed.")
        
        # Test some basic queries
        print("\n🔄 Testing created tables...")
        
        # Check tables
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"✅ Found {len(tables)} tables: {[table[0] for table in tables]}")
        
        # Check sample data
        cursor.execute("SELECT COUNT(*) FROM test_plans;")
        test_plans_count = cursor.fetchone()[0]
        print(f"✅ Test plans: {test_plans_count} records")
        
        cursor.execute("SELECT COUNT(*) FROM test_cases;")
        test_cases_count = cursor.fetchone()[0]
        print(f"✅ Test cases: {test_cases_count} records")
        
        cursor.execute("SELECT COUNT(*) FROM test_steps;")
        test_steps_count = cursor.fetchone()[0]
        print(f"✅ Test steps: {test_steps_count} records")
        
        cursor.execute("SELECT COUNT(*) FROM chat_messages;")
        chat_messages_count = cursor.fetchone()[0]
        print(f"✅ Chat messages: {chat_messages_count} records")
        
        # Show sample test plan
        print("\n📋 Sample test plan:")
        cursor.execute("""
            SELECT tp.plan_id, tp.title, COUNT(tc.id) as test_cases_count
            FROM test_plans tp
            LEFT JOIN test_cases tc ON tp.id = tc.test_plan_id
            WHERE tp.is_deleted = FALSE
            GROUP BY tp.id, tp.plan_id, tp.title
            LIMIT 1;
        """)
        
        sample = cursor.fetchone()
        if sample:
            print(f"   Plan ID: {sample[0]}")
            print(f"   Title: {sample[1]}")
            print(f"   Test Cases: {sample[2]}")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 Database setup completed successfully!")
        return True
        
    except FileNotFoundError:
        print("❌ Error: database-schema.sql file not found!")
        return False
    except Exception as e:
        print(f"❌ Error executing schema: {e}")
        return False

def main():
    """Main execution function"""
    print("🚀 Starting Test Plan Generator Database Setup")
    print("=" * 50)
    
    # Wait for database to be available
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"Attempt {attempt}/{max_attempts}")
        
        if test_connection():
            print("\n🎯 Database is ready! Proceeding with schema setup...")
            break
        else:
            if attempt < max_attempts:
                print("⏳ Database not ready yet, waiting 30 seconds...")
                time.sleep(30)
            else:
                print("❌ Database connection failed after maximum attempts")
                sys.exit(1)
    
    # Execute schema
    if execute_schema():
        print("\n✅ Setup completed successfully!")
        print("\n📊 Database is ready for use!")
        print("\n🔗 Connection details:")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   Database: {DB_CONFIG['database']}")
        print(f"   User: {DB_CONFIG['user']}")
        print(f"   Port: {DB_CONFIG['port']}")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
