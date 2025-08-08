from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import logging

from src.repositories.statement_repository import StatementRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.category_repository import CategoryRepository
from src.models.database_models import Statement, BankType, TransactionType
from src.parsers.axis_cc_parser import AxisCreditCardStatementParser
from src.parsers.axis_saving_parser import AxisSavingStatementParser

logger = logging.getLogger(__name__)

class StatementService:
    def __init__(self, session: Session):
        self.session = session
        self.statement_repo = StatementRepository(session)
        self.transaction_repo = TransactionRepository(session)
        self.category_repo = CategoryRepository(session)
        
        # Initialize parsers
        self.parsers = {
            BankType.AXIS_CREDIT: AxisCreditCardStatementParser(),
            BankType.AXIS_SAVINGS: AxisSavingStatementParser(),
        }
    
    def detect_bank_type(self, file_path: str) -> Optional[BankType]:
        """Detect bank type from file content or name"""
        try:
            # Try to extract text and detect based on content
            with open(file_path, 'rb') as f:
                content = f.read(1024).decode('utf-8', errors='ignore')
                
            file_name = Path(file_path).name.lower()
            
            # Check for Axis Bank indicators
            if 'axis' in content.lower() or 'axis' in file_name:
                if 'credit' in content.lower() or 'credit' in file_name:
                    return BankType.AXIS_CREDIT
                elif 'saving' in content.lower() or 'saving' in file_name:
                    return BankType.AXIS_SAVINGS
                else:
                    # Default to credit card for Axis
                    return BankType.AXIS_CREDIT
            
            # Add more bank detection logic here
            # For now, default to Axis Credit Card
            return BankType.AXIS_CREDIT
            
        except Exception as e:
            logger.error(f"Error detecting bank type for {file_path}: {str(e)}")
            return None
    
    def create_statement_record(self, user_id: int, file_path: str, 
                              bank_type: BankType = None) -> Optional[Statement]:
        """Create a statement record in the database"""
        try:
            file_path = str(Path(file_path).resolve())
            file_name = Path(file_path).name
            
            # Detect bank type if not provided
            if bank_type is None:
                bank_type = self.detect_bank_type(file_path)
                if bank_type is None:
                    logger.error(f"Could not detect bank type for {file_path}")
                    return None
            
            # Extract statement date from filename or use current date
            statement_date = self._extract_statement_date(file_name)
            
            # Create statement record
            statement = self.statement_repo.create_statement(
                user_id=user_id,
                file_path=file_path,
                file_name=file_name,
                bank_type=bank_type,
                statement_date=statement_date
            )
            
            return statement
            
        except Exception as e:
            logger.error(f"Error creating statement record: {str(e)}")
            return None
    
    def process_statement(self, statement_id: int) -> bool:
        """Process a statement and extract transactions"""
        try:
            # Get statement
            statement = self.statement_repo.get_statement_by_id(statement_id)
            if not statement:
                logger.error(f"Statement not found: {statement_id}")
                return False
            
            # Update status to processing
            self.statement_repo.update_parsing_status(statement_id, 'processing')
            
            # Get appropriate parser
            parser = self.parsers.get(statement.bank_type)
            if not parser:
                logger.error(f"No parser available for bank type: {statement.bank_type}")
                self.statement_repo.update_parsing_status(statement_id, 'failed', 
                                                        f"No parser for {statement.bank_type}")
                return False
            
            # Parse transactions
            transactions = parser.parse_statement(statement.file_path)
            if not transactions:
                logger.warning(f"No transactions found in statement: {statement.file_name}")
                self.statement_repo.update_parsing_status(statement_id, 'completed')
                return True
            
            # Convert to database format and save
            total_debits = 0.0
            total_credits = 0.0
            
            for txn in transactions:
                # Categorize transaction
                category = self.category_repo.categorize_transaction(statement.user_id, txn.description)
                
                # Convert transaction type
                txn_type = TransactionType.DEBIT if txn.is_debit else TransactionType.CREDIT
                
                # Create transaction record
                db_transaction = self.transaction_repo.create_transaction(
                    statement_id=statement_id,
                    transaction_date=txn.date,
                    description=txn.description,
                    amount=txn.amount,
                    transaction_type=txn_type,
                    category=category or txn.category
                )
                
                if db_transaction:
                    if txn.is_debit:
                        total_debits += txn.amount
                    else:
                        total_credits += txn.amount
            
            # Update statement summary
            self.statement_repo.update_statement_summary(
                statement_id=statement_id,
                total_debits=total_debits,
                total_credits=total_credits,
                transaction_count=len(transactions)
            )
            
            logger.info(f"Processed statement {statement.file_name}: {len(transactions)} transactions")
            return True
            
        except Exception as e:
            logger.error(f"Error processing statement {statement_id}: {str(e)}")
            self.statement_repo.update_parsing_status(statement_id, 'failed', str(e))
            return False
    
    def get_statement_summary(self, statement_id: int) -> Dict:
        """Get comprehensive statement summary"""
        statement = self.statement_repo.get_statement_by_id(statement_id)
        if not statement:
            return {}
        
        # Get transactions for this statement
        transactions = self.transaction_repo.get_transactions_by_statement(statement_id)
        
        # Calculate category breakdown
        category_summary = {}
        for txn in transactions:
            if txn.category:
                if txn.category not in category_summary:
                    category_summary[txn.category] = {'amount': 0.0, 'count': 0}
                category_summary[txn.category]['amount'] += txn.amount
                category_summary[txn.category]['count'] += 1
        
        return {
            'statement_id': statement.id,
            'file_name': statement.file_name,
            'bank_type': statement.bank_type.value,
            'statement_date': statement.statement_date.isoformat() if statement.statement_date else None,
            'parsing_status': statement.parsing_status,
            'total_debits': statement.total_debits,
            'total_credits': statement.total_credits,
            'transaction_count': statement.transaction_count,
            'opening_balance': statement.opening_balance,
            'closing_balance': statement.closing_balance,
            'category_summary': category_summary,
            'transactions_count': len(transactions)
        }
    
    def _extract_statement_date(self, file_name: str) -> datetime:
        """Extract statement date from filename"""
        try:
            # Try to extract date from filename patterns
            import re
            
            # Pattern for DD-MM-YYYY or DD-MM-YY
            date_patterns = [
                r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
                r'(\d{2})-(\d{2})-(\d{2})',  # DD-MM-YY
                r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, file_name)
                if match:
                    if len(match.groups()) == 3:
                        if len(match.group(3)) == 4:  # YYYY format
                            if pattern == r'(\d{4})-(\d{2})-(\d{2})':
                                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                            else:
                                return datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)))
                        else:  # YY format
                            year = 2000 + int(match.group(3))
                            return datetime(year, int(match.group(2)), int(match.group(1)))
            
            # If no date found, use current date
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"Could not extract date from filename {file_name}: {str(e)}")
            return datetime.now()
