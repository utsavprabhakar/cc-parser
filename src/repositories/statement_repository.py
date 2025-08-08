from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from datetime import datetime
import logging

from src.models.database_models import Statement, BankType

logger = logging.getLogger(__name__)

class StatementRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create_statement(self, user_id: int, file_path: str, file_name: str, 
                        bank_type: BankType, statement_date: datetime,
                        opening_balance: float = None, closing_balance: float = None) -> Optional[Statement]:
        """Create a new statement record"""
        try:
            statement = Statement(
                user_id=user_id,
                file_path=file_path,
                file_name=file_name,
                bank_type=bank_type,
                statement_date=statement_date,
                opening_balance=opening_balance,
                closing_balance=closing_balance
            )
            self.session.add(statement)
            self.session.commit()
            self.session.refresh(statement)
            logger.info(f"Created statement: {file_name}")
            return statement
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating statement {file_name}: {str(e)}")
            return None
    
    def get_statement_by_id(self, statement_id: int) -> Optional[Statement]:
        """Get statement by ID"""
        return self.session.query(Statement).filter(Statement.id == statement_id).first()
    
    def get_statements_by_user(self, user_id: int, limit: int = None) -> List[Statement]:
        """Get all statements for a user"""
        query = self.session.query(Statement).filter(Statement.user_id == user_id).order_by(desc(Statement.statement_date))
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_statements_by_bank_type(self, user_id: int, bank_type: BankType) -> List[Statement]:
        """Get statements by bank type for a user"""
        return self.session.query(Statement).filter(
            and_(Statement.user_id == user_id, Statement.bank_type == bank_type)
        ).order_by(desc(Statement.statement_date)).all()
    
    def get_statements_by_date_range(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Statement]:
        """Get statements within a date range"""
        return self.session.query(Statement).filter(
            and_(
                Statement.user_id == user_id,
                Statement.statement_date >= start_date,
                Statement.statement_date <= end_date
            )
        ).order_by(desc(Statement.statement_date)).all()
    
    def update_statement_summary(self, statement_id: int, total_debits: float, 
                               total_credits: float, transaction_count: int) -> Optional[Statement]:
        """Update statement summary after parsing"""
        try:
            statement = self.get_statement_by_id(statement_id)
            if not statement:
                return None
            
            statement.total_debits = total_debits
            statement.total_credits = total_credits
            statement.transaction_count = transaction_count
            statement.parsing_status = 'completed'
            
            self.session.commit()
            self.session.refresh(statement)
            logger.info(f"Updated statement summary: {statement.file_name}")
            return statement
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating statement summary {statement_id}: {str(e)}")
            return None
    
    def update_parsing_status(self, statement_id: int, status: str, errors: str = None) -> Optional[Statement]:
        """Update parsing status"""
        try:
            statement = self.get_statement_by_id(statement_id)
            if not statement:
                return None
            
            statement.parsing_status = status
            if errors:
                statement.parsing_errors = errors
            
            self.session.commit()
            self.session.refresh(statement)
            logger.info(f"Updated parsing status for {statement.file_name}: {status}")
            return statement
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating parsing status {statement_id}: {str(e)}")
            return None
    
    def delete_statement(self, statement_id: int) -> bool:
        """Delete a statement and its transactions"""
        try:
            statement = self.get_statement_by_id(statement_id)
            if not statement:
                return False
            
            self.session.delete(statement)
            self.session.commit()
            logger.info(f"Deleted statement: {statement.file_name}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting statement {statement_id}: {str(e)}")
            return False
    
    def get_statement_stats(self, user_id: int) -> dict:
        """Get statistics for user's statements"""
        statements = self.get_statements_by_user(user_id)
        
        if not statements:
            return {
                'total_statements': 0,
                'total_transactions': 0,
                'total_debits': 0.0,
                'total_credits': 0.0,
                'bank_types': {}
            }
        
        total_transactions = sum(s.transaction_count for s in statements)
        total_debits = sum(s.total_debits for s in statements)
        total_credits = sum(s.total_credits for s in statements)
        
        # Count by bank type
        bank_types = {}
        for statement in statements:
            bank_type = statement.bank_type.value
            if bank_type not in bank_types:
                bank_types[bank_type] = 0
            bank_types[bank_type] += 1
        
        return {
            'total_statements': len(statements),
            'total_transactions': total_transactions,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'bank_types': bank_types
        }
