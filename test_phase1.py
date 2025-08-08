#!/usr/bin/env python3
"""
Test script for Phase 1 functionality
"""

import sys
from pathlib import Path
import logging

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent))

from src.database.session import get_db_session, get_database_manager
from src.services.user_service import UserService
from src.services.statement_service import StatementService
from src.services.transaction_service import TransactionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_initialization():
    """Test database initialization"""
    print("🔧 Testing database initialization...")
    try:
        db_manager = get_database_manager()
        db_info = db_manager.get_database_info()
        print(f"✅ Database Status: {db_info.get('status')}")
        print(f"✅ Database URL: {db_info.get('database_url')}")
        print(f"✅ Tables: {', '.join(db_info.get('tables', []))}")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False

def test_user_creation():
    """Test user creation"""
    print("\n👤 Testing user creation...")
    try:
        with get_db_session() as session:
            user_service = UserService(session)
            
            # Create test user
            user = user_service.create_user("test_user", "test@example.com")
            if user:
                print(f"✅ Created user: {user.username} (ID: {user.id})")
                
                # Get user summary
                summary = user_service.get_user_summary(user.id)
                print(f"✅ User categories: {summary.get('categories_count')}")
                print(f"✅ User mappings: {summary.get('category_mappings_count')}")
                return user.id
            else:
                print("❌ Failed to create user")
                return None
    except Exception as e:
        print(f"❌ User creation failed: {str(e)}")
        return None

def test_statement_processing(user_id: int):
    """Test statement processing"""
    print("\n📄 Testing statement processing...")
    
    # Check if test statement exists
    test_statement = Path("data/statements/AXISMB_24-11-2024.pdf")
    if not test_statement.exists():
        print(f"❌ Test statement not found: {test_statement}")
        return None
    
    try:
        with get_db_session() as session:
            statement_service = StatementService(session)
            transaction_service = TransactionService(session)
            
            # Create statement record
            statement = statement_service.create_statement_record(user_id, str(test_statement))
            if not statement:
                print("❌ Failed to create statement record")
                return None
            
            print(f"✅ Created statement record: {statement.file_name}")
            print(f"✅ Bank type: {statement.bank_type.value}")
            
            # Process statement
            success = statement_service.process_statement(statement.id)
            if not success:
                print("❌ Failed to process statement")
                return None
            
            print("✅ Statement processed successfully")
            
            # Get summary
            summary = statement_service.get_statement_summary(statement.id)
            print(f"✅ Transactions: {summary['transaction_count']}")
            print(f"✅ Total spending: ₹{summary['total_debits']:,.2f}")
            
            # Get spending analysis
            analysis = transaction_service.get_spending_analysis(user_id)
            print(f"✅ Overall spending: ₹{analysis['summary']['total_spending']:,.2f}")
            
            return statement.id
            
    except Exception as e:
        print(f"❌ Statement processing failed: {str(e)}")
        return None

def test_analytics(user_id: int):
    """Test analytics functionality"""
    print("\n📊 Testing analytics...")
    try:
        with get_db_session() as session:
            transaction_service = TransactionService(session)
            
            # Get categories
            categories = transaction_service.get_user_categories(user_id)
            print(f"✅ User categories: {len(categories)}")
            
            # Get category mappings
            mappings = transaction_service.get_category_mappings(user_id)
            print(f"✅ Category mappings: {len(mappings)}")
            
            # Get spending analysis
            analysis = transaction_service.get_spending_analysis(user_id)
            if analysis['summary']['total_spending'] > 0:
                print(f"✅ Total spending: ₹{analysis['summary']['total_spending']:,.2f}")
                print(f"✅ Total transactions: {analysis['summary']['total_transactions']}")
                
                if analysis['top_categories']:
                    print("✅ Top categories:")
                    for category, data in list(analysis['top_categories'].items())[:3]:
                        print(f"   - {category}: ₹{data['total_amount']:,.2f}")
            
            return True
            
    except Exception as e:
        print(f"❌ Analytics failed: {str(e)}")
        return False

def cleanup_test_data(user_id: int):
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        with get_db_session() as session:
            user_service = UserService(session)
            user_service.delete_user(user_id)
            print("✅ Test data cleaned up")
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Starting Phase 1 functionality tests...")
    print("=" * 50)
    
    # Test 1: Database initialization
    if not test_database_initialization():
        print("❌ Database test failed. Exiting.")
        return
    
    # Test 2: User creation
    user_id = test_user_creation()
    if not user_id:
        print("❌ User creation test failed. Exiting.")
        return
    
    # Test 3: Statement processing
    statement_id = test_statement_processing(user_id)
    if not statement_id:
        print("❌ Statement processing test failed.")
        # Continue with analytics test anyway
    
    # Test 4: Analytics
    analytics_success = test_analytics(user_id)
    
    # Cleanup
    cleanup_test_data(user_id)
    
    print("\n" + "=" * 50)
    if statement_id and analytics_success:
        print("🎉 All tests passed! Phase 1 is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n📝 Next steps:")
    print("1. Try the CLI tool: python cli.py --help")
    print("2. Create a user: python cli.py create-user yourname your@email.com")
    print("3. Process a statement: python cli.py process data/statements/AXISMB_24-11-2024.pdf yourname")

if __name__ == '__main__':
    main()
