from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging

from src.repositories.transaction_repository import TransactionRepository
from src.repositories.category_repository import CategoryRepository
from src.models.database_models import TransactionType

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self, session: Session):
        self.session = session
        self.transaction_repo = TransactionRepository(session)
        self.category_repo = CategoryRepository(session)
    
    def get_user_transactions(self, user_id: int, limit: int = None) -> List[Dict]:
        """Get transactions for a user with formatted data"""
        transactions = self.transaction_repo.get_transactions_by_user(user_id, limit)
        
        formatted_transactions = []
        for txn in transactions:
            formatted_transactions.append({
                'id': txn.id,
                'date': txn.transaction_date.isoformat() if txn.transaction_date else None,
                'description': txn.description,
                'amount': txn.amount,
                'transaction_type': txn.transaction_type.value,
                'category': txn.category,
                'is_categorized_by_llm': txn.is_categorized_by_llm,
                'user_corrected': txn.user_corrected,
                'statement_id': txn.statement_id
            })
        
        return formatted_transactions
    
    def get_transactions_by_category(self, user_id: int, category: str) -> List[Dict]:
        """Get transactions by category for a user"""
        transactions = self.transaction_repo.get_transactions_by_category(user_id, category)
        
        formatted_transactions = []
        for txn in transactions:
            formatted_transactions.append({
                'id': txn.id,
                'date': txn.transaction_date.isoformat() if txn.transaction_date else None,
                'description': txn.description,
                'amount': txn.amount,
                'transaction_type': txn.transaction_type.value,
                'category': txn.category,
                'statement_id': txn.statement_id
            })
        
        return formatted_transactions
    
    def get_transactions_by_date_range(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get transactions within a date range"""
        transactions = self.transaction_repo.get_transactions_by_date_range(user_id, start_date, end_date)
        
        formatted_transactions = []
        for txn in transactions:
            formatted_transactions.append({
                'id': txn.id,
                'date': txn.transaction_date.isoformat() if txn.transaction_date else None,
                'description': txn.description,
                'amount': txn.amount,
                'transaction_type': txn.transaction_type.value,
                'category': txn.category,
                'statement_id': txn.statement_id
            })
        
        return formatted_transactions
    
    def update_transaction_category(self, transaction_id: int, category: str) -> bool:
        """Update transaction category (user correction)"""
        transaction = self.transaction_repo.update_transaction_category(transaction_id, category)
        return transaction is not None
    
    def get_spending_analysis(self, user_id: int, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """Get comprehensive spending analysis"""
        # Get category summary
        category_summary = self.transaction_repo.get_category_summary(user_id, start_date, end_date)
        
        # Get monthly summary
        if start_date:
            year = start_date.year
        else:
            year = datetime.now().year
        
        monthly_summary = self.transaction_repo.get_monthly_summary(user_id, year)
        
        # Calculate totals
        total_spending = sum(cat['total_amount'] for cat in category_summary.values())
        total_transactions = sum(cat['transaction_count'] for cat in category_summary.values())
        
        # Get top spending categories
        top_categories = sorted(
            category_summary.items(),
            key=lambda x: x[1]['total_amount'],
            reverse=True
        )[:5]
        
        return {
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'summary': {
                'total_spending': total_spending,
                'total_transactions': total_transactions,
                'average_transaction': total_spending / total_transactions if total_transactions > 0 else 0
            },
            'category_breakdown': category_summary,
            'top_categories': dict(top_categories),
            'monthly_trend': monthly_summary
        }
    
    def get_monthly_comparison(self, user_id: int, month1: str, month2: str) -> Dict:
        """Compare spending between two months (format: YYYY-MM)"""
        try:
            # Parse months
            date1 = datetime.strptime(month1, '%Y-%m')
            date2 = datetime.strptime(month2, '%Y-%m')
            
            # Get start and end dates for each month
            start1 = date1.replace(day=1)
            end1 = (start1 + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            start2 = date2.replace(day=1)
            end2 = (start2 + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Get spending analysis for each month
            analysis1 = self.get_spending_analysis(user_id, start1, end1)
            analysis2 = self.get_spending_analysis(user_id, start2, end2)
            
            # Calculate differences
            spending_diff = analysis2['summary']['total_spending'] - analysis1['summary']['total_spending']
            spending_change_pct = (spending_diff / analysis1['summary']['total_spending'] * 100) if analysis1['summary']['total_spending'] > 0 else 0
            
            return {
                'month1': {
                    'month': month1,
                    'spending': analysis1['summary']['total_spending'],
                    'transactions': analysis1['summary']['total_transactions'],
                    'categories': analysis1['category_breakdown']
                },
                'month2': {
                    'month': month2,
                    'spending': analysis2['summary']['total_spending'],
                    'transactions': analysis2['summary']['total_transactions'],
                    'categories': analysis2['category_breakdown']
                },
                'comparison': {
                    'spending_difference': spending_diff,
                    'spending_change_percentage': spending_change_pct,
                    'transaction_difference': analysis2['summary']['total_transactions'] - analysis1['summary']['total_transactions']
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing months {month1} and {month2}: {str(e)}")
            return {}
    
    def get_user_categories(self, user_id: int) -> List[str]:
        """Get all categories used by a user"""
        return self.category_repo.get_categories_by_user(user_id)
    
    def add_category_mapping(self, user_id: int, pattern: str, category: str, 
                           is_regex: bool = False, priority: int = 0) -> bool:
        """Add a new category mapping for a user"""
        mapping = self.category_repo.create_category_mapping(user_id, pattern, category, is_regex, priority)
        return mapping is not None
    
    def get_category_mappings(self, user_id: int) -> List[Dict]:
        """Get all category mappings for a user"""
        mappings = self.category_repo.get_category_mappings_by_user(user_id)
        
        formatted_mappings = []
        for mapping in mappings:
            formatted_mappings.append({
                'id': mapping.id,
                'pattern': mapping.pattern,
                'category': mapping.category,
                'is_regex': mapping.is_regex,
                'priority': mapping.priority,
                'is_active': mapping.is_active
            })
        
        return formatted_mappings
