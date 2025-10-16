#!/usr/bin/env python3
import pymysql
import sys

# Test both passwords
passwords = ['TempPassword123!', 'TempPassword123']

for password in passwords:
    try:
        print(f"Testing password: {password}")
        connection = pymysql.connect(
            host='test-plan-generator-db.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
            user='admin',
            password=password,
            database='testplangenerator',
            port=3306,
            connect_timeout=10
        )
        print(f"✅ SUCCESS with password: {password}")
        connection.close()
        sys.exit(0)
    except Exception as e:
        print(f"❌ FAILED with password {password}: {e}")

print("Both passwords failed")
