import sys
from pathlib import Path
import os
import pandas as pd
from datetime import datetime
import logging

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.session import get_db_session
from src.services.user_service import UserService
from src.services.statement_service import StatementService
from src.services.transaction_service import TransactionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_statement_with_db(pdf_path: str, username: str = "default_user") -> None:
    """
    Analyze statement using the new database-backed architecture
    
    Args:
        pdf_path: Path to the PDF statement
        username: Username for the analysis (creates user if doesn't exist)
    """
    try:
        with get_db_session() as session:
            # Initialize services
            user_service = UserService(session)
            statement_service = StatementService(session)
            transaction_service = TransactionService(session)
            
            # Get or create user
            user = user_service.get_user_by_username(username)
            if not user:
                logger.info(f"Creating new user: {username}")
                user = user_service.create_user(username, f"{username}@example.com")
                if not user:
                    logger.error("Failed to create user")
                    return
            
            logger.info(f"Using user: {user.username} (ID: {user.id})")
            
            # Create statement record
            logger.info(f"Creating statement record for: {pdf_path}")
            statement = statement_service.create_statement_record(user.id, pdf_path)
            if not statement:
                logger.error("Failed to create statement record")
                return
            
            # Process statement
            logger.info(f"Processing statement: {statement.file_name}")
            success = statement_service.process_statement(statement.id)
            if not success:
                logger.error("Failed to process statement")
                return
            
            # Get statement summary
            summary = statement_service.get_statement_summary(statement.id)
            
            # Print analysis
            print("\n=== Statement Analysis ===")
            print(f"File: {summary['file_name']}")
            print(f"Bank Type: {summary['bank_type']}")
            print(f"Statement Date: {summary['statement_date']}")
            print(f"Status: {summary['parsing_status']}")
            print(f"\nTotal Spending: ₹{summary['total_debits']:,.2f}")
            print(f"Total Credits: ₹{summary['total_credits']:,.2f}")
            print(f"Transaction Count: {summary['transaction_count']}")
            
            if summary['category_summary']:
                print(f"\nSpending by Category:")
                for category, data in summary['category_summary'].items():
                    print(f"  {category}: ₹{data['amount']:,.2f} ({data['count']} transactions)")
            
            # Get user's overall spending analysis
            logger.info("Getting overall spending analysis...")
            spending_analysis = transaction_service.get_spending_analysis(user.id)
            
            if spending_analysis['summary']['total_spending'] > 0:
                print(f"\n=== Overall Spending Analysis ===")
                print(f"Total Spending: ₹{spending_analysis['summary']['total_spending']:,.2f}")
                print(f"Total Transactions: {spending_analysis['summary']['total_transactions']}")
                print(f"Average Transaction: ₹{spending_analysis['summary']['average_transaction']:,.2f}")
                
                if spending_analysis['top_categories']:
                    print(f"\nTop Spending Categories:")
                    for category, data in spending_analysis['top_categories'].items():
                        print(f"  {category}: ₹{data['total_amount']:,.2f}")
            
            # Save to Excel (legacy functionality)
            save_to_excel(summary, pdf_path)
            
    except Exception as e:
        logger.error(f"Error analyzing statement: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def save_to_excel(summary: dict, original_pdf_path: str) -> None:
    """Save analysis to Excel file (legacy functionality)"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(original_pdf_path).parent / f"statement_analysis_{timestamp}.xlsx"
        
        # Create DataFrame from summary data
        if summary['category_summary']:
            category_data = []
            for category, data in summary['category_summary'].items():
                category_data.append({
                    'Category': category,
                    'Total': data['amount'],
                    'Count': data['count']
                })
            
            df_categories = pd.DataFrame(category_data)
        else:
            df_categories = pd.DataFrame(columns=['Category', 'Total', 'Count'])
        
        # Create summary data
        summary_data = {
            'Metric': [
                'Total Debits', 'Total Credits', 'Net Flow', 
                'Transaction Count', 'Bank Type', 'Statement Date'
            ],
            'Value': [
                f"₹{summary['total_debits']:,.2f}",
                f"₹{summary['total_credits']:,.2f}",
                f"₹{(summary['total_credits'] - summary['total_debits']):,.2f}",
                summary['transaction_count'],
                summary['bank_type'],
                summary['statement_date'] or 'N/A'
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        
        # Save to Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_categories.to_excel(writer, sheet_name='Category Summary', index=False)
            df_summary.to_excel(writer, sheet_name='Overall Summary', index=False)
        
        print(f"\nDetailed analysis saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving to Excel: {str(e)}")

def analyze_statement(pdf_path: str) -> None:
    """
    Legacy function for backward compatibility
    """
    logger.info("Using legacy analyze_statement function")
    analyze_statement_with_db(pdf_path)

def get_database_info() -> dict:
    """Get database information"""
    try:
        from src.database.session import get_database_manager
        db_manager = get_database_manager()
        return db_manager.get_database_info()
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/main.py <path-to-pdf>")
        print("\nDatabase-backed analysis will be performed.")
        print("A default user will be created if needed.")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    # Show database info
    db_info = get_database_info()
    print(f"Database Status: {db_info.get('status', 'unknown')}")
    
    analyze_statement_with_db(pdf_path)