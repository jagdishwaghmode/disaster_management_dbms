import mysql.connector
from mysql.connector import Error

try:
    # Connect to MySQL server
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root123'
    )
    
    if conn.is_connected():
        print("Connected to MySQL server")
        
        # Create a cursor object
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS disaster_management")
        print("Database 'disaster_management' created or already exists")
        
        # Switch to the database
        cursor.execute("USE disaster_management")
        
        # Check if any tables exist
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"Found {len(tables)} existing tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("No tables found in the database")
            
except Error as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()
        print("MySQL connection closed") 