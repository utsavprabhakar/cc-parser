from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import Optional, List, Dict
from datetime import datetime
import logging

from src.models.database_models import Transaction, TransactionType

logger = logging.getLogger(__name__)

class TransactionRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create_transaction(self, statement_id: int, transaction_date: datetime, 
                          description: str, amount: float, transaction_type: TransactionType,
                          category: str = None, original_category: str = None,
                          is_categorized_by_llm: bool = False, llm_confidence: float = None) -> Optional[Transaction]:
        """Create a new transaction"""
        try:
            transaction = Transaction(
                statement_id=statement_id,
                transaction_date=transaction_date,
                description=description,
                amount=amount,
                transaction_type=transaction_type,
                category=category,
                original_category=original_category,
                is_categorized_by_llm=is_categorized_by_llm,
                llm_confidence=llm_confidence
            )
            self.session.add(transaction)
            self.session.commit()
            self.session.refresh(transaction)
            return transaction
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating transaction: {str(e)}")
            return None
    
    def create_bulk_transactions(self, transactions_data: List[Dict]) -> List[Transaction]:
        """Create multiple transactions in bulk"""
        try:
            transactions = []
            for data in transactions_data:
                transaction = Transaction(**data)
                transactions.append(transaction)
            
            self.session.add_all(transactions)
            self.session.commit()
            
            # Refresh all transactions
            for transaction in transactions:
                self.session.refresh(transaction)
            
            logger.info(f"Created {len(transactions)} transactions in bulk")
            return transactions
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating bulk transactions: {str(e)}")
            return []
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        return self.session.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    def get_transactions_by_statement(self, statement_id: int) -> List[Transaction]:
        """Get all transactions for a statement"""
        return self.session.query(Transaction).filter(
            Transaction.statement_id == statement_id
        ).order_by(desc(Transaction.transaction_date)).all()
    
    def get_transactions_by_user(self, user_id: int, limit: int = None) -> List[Transaction]:
        """Get all transactions for a user (across all statements)"""
        query = self.session.query(Transaction).join(
            Transaction.statement
        ).filter(
            Transaction.statement.has(user_id=user_id)
        ).order_by(desc(Transaction.transaction_date))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_transactions_by_category(self, user_id: int, category: str) -> List[Transaction]:
        """Get transactions by category for a user"""
        return self.session.query(Transaction).join(
            Transaction.statement
        ).filter(
            and_(
                Transaction.statement.has(user_id=user_id),
                Transaction.category == category
            )
        ).order_by(desc(Transaction.transaction_date)).all()
    
    def get_transactions_by_date_range(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Get transactions within a date range"""
        return self.session.query(Transaction).join(
            Transaction.statement
        ).filter(
            and_(
                Transaction.statement.has(user_id=user_id),
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        ).order_by(desc(Transaction.transaction_date)).all()
    
    def update_transaction_category(self, transaction_id: int, category: str, 
                                  user_corrected: bool = True) -> Optional[Transaction]:
        """Update transaction category (for user corrections)"""
        try:
            transaction = self.get_transaction_by_id(transaction_id)
            if not transaction:
                return None
            
            # Store original category if not already stored
            if not transaction.original_category:
                transaction.original_category = transaction.category
            
            transaction.category = category
            transaction.user_corrected = user_corrected
            
            self.session.commit()
            self.session.refresh(transaction)
            logger.info(f"Updated transaction category: {transaction_id}")
            return transaction
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating transaction category {transaction_id}: {str(e)}")
            return None
    
    def get_category_summary(self, user_id: int, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """Get spending summary by category"""
        query = self.session.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).join(
            Transaction.statement
        ).filter(
            and_(
                Transaction.statement.has(user_id=user_id),
                Transaction.transaction_type == TransactionType.DEBIT
            )
        )
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        results = query.group_by(Transaction.category).all()
        
        summary = {}
        for category, total_amount, count in results:
            if category:
                summary[category] = {
                    'total_amount': float(total_amount),
                    'transaction_count': count
                }
        
        return summary
    
    def get_monthly_summary(self, user_id: int, year: int = None) -> Dict:
        """Get monthly spending summary"""
        query = self.session.query(
            func.strftime('%Y-%m', Transaction.transaction_date).label('month'),
            func.sum(Transaction.amount).label('debit_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).join(
            Transaction.statement
        ).filter(
            Transaction.statement.has(user_id=user_id)
        )
        
        if year:
            query = query.filter(func.strftime('%Y', Transaction.transaction_date) == str(year))
        
        results = query.group_by(
            func.strftime('%Y-%m', Transaction.transaction_date)
        ).order_by('month').all()
        
        monthly_summary = {}
        for month, debit_amount, count in results:
            monthly_summary[month] = {
                'debit_amount': float(debit_amount),
                'transaction_count': count
            }
        
        return monthly_summary
    
    def delete_transactions_by_statement(self, statement_id: int) -> bool:
        """Delete all transactions for a statement"""
        try:
            deleted_count = self.session.query(Transaction).filter(
                Transaction.statement_id == statement_id
            ).delete()
            
            self.session.commit()
            logger.info(f"Deleted {deleted_count} transactions for statement {statement_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting transactions for statement {statement_id}: {str(e)}")
            return False
