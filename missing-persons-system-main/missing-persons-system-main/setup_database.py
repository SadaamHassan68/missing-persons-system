import pymysql
from app import app, db

def setup_database():
    try:
        # Create database connection
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='',  # Add your MySQL password here
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            # Create database if not exists
            cursor.execute("CREATE DATABASE IF NOT EXISTS missing_persons")
            cursor.execute("USE missing_persons")
            
            # Drop existing tables if they exist
            cursor.execute("DROP TABLE IF EXISTS core_alert")
            cursor.execute("DROP TABLE IF EXISTS core_matchreport")
            cursor.execute("DROP TABLE IF EXISTS core_missingperson")
            cursor.execute("DROP TABLE IF EXISTS user")
            
            # Read and execute the SQL file
            with open('database_setup.sql', 'r') as sql_file:
                sql_commands = sql_file.read()
                for command in sql_commands.split(';'):
                    if command.strip():
                        try:
                            cursor.execute(command)
                        except pymysql.err.OperationalError as e:
                            if "Duplicate key name" not in str(e):
                                raise
                            print(f"Warning: {str(e)}")
            
            conn.commit()
            print("Database setup completed successfully!")
            
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    with app.app_context():
        setup_database() 