"""
Database migration script
"""

import os
import sys
from models import DatabaseConnection, migrate_database

def main():
    print("=" * 60)
    print("DATABASE MIGRATION")
    print("=" * 60)
    
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("Using SQLite database")
        database_url = 'sqlite:///chatbot.db'
    
    try:
        print("\n1. Testing connection...")
        db = DatabaseConnection(database_url)
        
        if db.test_connection():
            print("   Database connected!")
        else:
            print("   Connection failed!")
            sys.exit(1)
        
        print("\n2. Running migrations...")
        if migrate_database():
            print("   Migrations complete!")
        else:
            print("   Migrations failed!")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE!")
        print("=" * 60)
        
        return 0
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())