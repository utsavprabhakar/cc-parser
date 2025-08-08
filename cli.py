#!/usr/bin/env python3
"""
CLI tool for CC Parser with database-backed functionality
"""

import argparse
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database"""
    try:
        db_manager = get_database_manager()
        db_info = db_manager.get_database_info()
        print(f"Database Status: {db_info.get('status', 'unknown')}")
        if db_info.get('status') == 'connected':
            print(f"Database: {db_info.get('database_url', 'unknown')}")
            print(f"Tables: {', '.join(db_info.get('tables', []))}")
        return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

def create_user(username: str, email: str):
    """Create a new user"""
    try:
        with get_db_session() as session:
            user_service = UserService(session)
            user = user_service.create_user(username, email)
            if user:
                print(f"✅ Created user: {username} (ID: {user.id})")
                summary = user_service.get_user_summary(user.id)
                print(f"   Categories: {summary.get('categories_count', 0)}")
                print(f"   Mappings: {summary.get('category_mappings_count', 0)}")
            else:
                print(f"❌ Failed to create user: {username}")
    except Exception as e:
        print(f"Error creating user: {str(e)}")

def list_users():
    """List all users"""
    try:
        with get_db_session() as session:
            user_service = UserService(session)
            users = user_service.get_all_users()
            
            if not users:
                print("No users found.")
                return
            
            print(f"\nFound {len(users)} users:")
            print("-" * 60)
            for user in users:
                summary = user_service.get_user_summary(user.id)
                print(f"ID: {user.id}")
                print(f"Username: {user.username}")
                print(f"Email: {user.email}")
                print(f"Active: {user.is_active}")
                print(f"Categories: {summary.get('categories_count', 0)}")
                print(f"Created: {user.created_at}")
                print("-" * 60)
    except Exception as e:
        print(f"Error listing users: {str(e)}")

def process_statement(pdf_path: str, username: str):
    """Process a statement for a user"""
    try:
        if not Path(pdf_path).exists():
            print(f"❌ File not found: {pdf_path}")
            return
        
        with get_db_session() as session:
            user_service = UserService(session)
            statement_service = StatementService(session)
            transaction_service = TransactionService(session)
            
            # Get or create user
            user = user_service.get_user_by_username(username)
            if not user:
                print(f"❌ User not found: {username}")
                print("Use 'create-user' command to create a user first.")
                return
            
            print(f"📊 Processing statement for user: {username}")
            
            # Create statement record
            statement = statement_service.create_statement_record(user.id, pdf_path)
            if not statement:
                print("❌ Failed to create statement record")
                return
            
            print(f"📄 Statement: {statement.file_name}")
            print(f"🏦 Bank Type: {statement.bank_type.value}")
            
            # Process statement
            success = statement_service.process_statement(statement.id)
            if not success:
                print("❌ Failed to process statement")
                return
            
            # Get summary
            summary = statement_service.get_statement_summary(statement.id)
            
            print(f"\n✅ Statement processed successfully!")
            print(f"💰 Total Spending: ₹{summary['total_debits']:,.2f}")
            print(f"💳 Total Credits: ₹{summary['total_credits']:,.2f}")
            print(f"📝 Transactions: {summary['transaction_count']}")
            
            if summary['category_summary']:
                print(f"\n📊 Spending by Category:")
                for category, data in summary['category_summary'].items():
                    print(f"   {category}: ₹{data['amount']:,.2f} ({data['count']} transactions)")
            
            # Get overall analysis
            spending_analysis = transaction_service.get_spending_analysis(user.id)
            if spending_analysis['summary']['total_spending'] > 0:
                print(f"\n📈 Overall Analysis:")
                print(f"   Total Spending: ₹{spending_analysis['summary']['total_spending']:,.2f}")
                print(f"   Total Transactions: {spending_analysis['summary']['total_transactions']}")
                print(f"   Average Transaction: ₹{spending_analysis['summary']['average_transaction']:,.2f}")
                
    except Exception as e:
        print(f"Error processing statement: {str(e)}")
        logger.error(f"Error processing statement: {str(e)}", exc_info=True)

def show_analysis(username: str, month1: str = None, month2: str = None):
    """Show spending analysis for a user"""
    try:
        with get_db_session() as session:
            user_service = UserService(session)
            transaction_service = TransactionService(session)
            
            # Get user
            user = user_service.get_user_by_username(username)
            if not user:
                print(f"❌ User not found: {username}")
                return
            
            print(f"📊 Analysis for user: {username}")
            
            if month1 and month2:
                # Monthly comparison
                comparison = transaction_service.get_monthly_comparison(user.id, month1, month2)
                if comparison:
                    print(f"\n📅 Monthly Comparison: {month1} vs {month2}")
                    print(f"   {month1}: ₹{comparison['month1']['spending']:,.2f}")
                    print(f"   {month2}: ₹{comparison['month2']['spending']:,.2f}")
                    print(f"   Difference: ₹{comparison['comparison']['spending_difference']:,.2f}")
                    print(f"   Change: {comparison['comparison']['spending_change_percentage']:.1f}%")
                else:
                    print("❌ No data available for comparison")
            else:
                # Overall analysis
                analysis = transaction_service.get_spending_analysis(user.id)
                if analysis['summary']['total_spending'] > 0:
                    print(f"\n💰 Total Spending: ₹{analysis['summary']['total_spending']:,.2f}")
                    print(f"📝 Total Transactions: {analysis['summary']['total_transactions']}")
                    print(f"📊 Average Transaction: ₹{analysis['summary']['average_transaction']:,.2f}")
                    
                    if analysis['top_categories']:
                        print(f"\n🏆 Top Spending Categories:")
                        for category, data in analysis['top_categories'].items():
                            print(f"   {category}: ₹{data['total_amount']:,.2f}")
                else:
                    print("❌ No spending data available")
            
    except Exception as e:
        print(f"Error showing analysis: {str(e)}")

def list_categories(username: str):
    """List categories for a user"""
    try:
        with get_db_session() as session:
            user_service = UserService(session)
            transaction_service = TransactionService(session)
            
            # Get user
            user = user_service.get_user_by_username(username)
            if not user:
                print(f"❌ User not found: {username}")
                return
            
            categories = transaction_service.get_user_categories(user.id)
            mappings = transaction_service.get_category_mappings(user.id)
            
            print(f"📊 Categories for user: {username}")
            print(f"   Total Categories: {len(categories)}")
            print(f"   Total Mappings: {len(mappings)}")
            
            if categories:
                print(f"\n📋 Categories:")
                for category in sorted(categories):
                    print(f"   • {category}")
            
            if mappings:
                print(f"\n🔗 Category Mappings:")
                for mapping in mappings[:10]:  # Show first 10
                    print(f"   • '{mapping['pattern']}' → {mapping['category']}")
                if len(mappings) > 10:
                    print(f"   ... and {len(mappings) - 10} more")
            
    except Exception as e:
        print(f"Error listing categories: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='CC Parser CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init database command
    subparsers.add_parser('init-db', help='Initialize database')
    
    # User management commands
    create_user_parser = subparsers.add_parser('create-user', help='Create a new user')
    create_user_parser.add_argument('username', help='Username')
    create_user_parser.add_argument('email', help='Email address')
    
    subparsers.add_parser('list-users', help='List all users')
    
    # Statement processing commands
    process_parser = subparsers.add_parser('process', help='Process a statement')
    process_parser.add_argument('pdf_path', help='Path to PDF statement')
    process_parser.add_argument('username', help='Username')
    
    # Analysis commands
    analysis_parser = subparsers.add_parser('analyze', help='Show spending analysis')
    analysis_parser.add_argument('username', help='Username')
    analysis_parser.add_argument('--month1', help='First month (YYYY-MM)')
    analysis_parser.add_argument('--month2', help='Second month (YYYY-MM)')
    
    categories_parser = subparsers.add_parser('categories', help='List categories')
    categories_parser.add_argument('username', help='Username')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize database for all commands
    if not init_database():
        print("❌ Failed to initialize database")
        return
    
    # Execute commands
    if args.command == 'init-db':
        print("✅ Database initialized successfully")
    
    elif args.command == 'create-user':
        create_user(args.username, args.email)
    
    elif args.command == 'list-users':
        list_users()
    
    elif args.command == 'process':
        process_statement(args.pdf_path, args.username)
    
    elif args.command == 'analyze':
        show_analysis(args.username, args.month1, args.month2)
    
    elif args.command == 'categories':
        list_categories(args.username)

if __name__ == '__main__':
    main()
