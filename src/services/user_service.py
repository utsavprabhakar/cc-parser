from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import logging

from src.repositories.user_repository import UserRepository
from src.repositories.category_repository import CategoryRepository
from src.models.database_models import User

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.category_repo = CategoryRepository(session)
    
    def create_user(self, username: str, email: str) -> Optional[User]:
        """Create a new user with default category mappings"""
        try:
            # Create user
            user = self.user_repo.create_user(username, email)
            if not user:
                return None
            
            # Import default category mappings
            self.category_repo.import_default_categories(user.id)
            
            logger.info(f"Created user {username} with default categories")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user {username}: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.user_repo.get_user_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.user_repo.get_user_by_username(username)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.user_repo.get_user_by_email(email)
    
    def get_all_users(self) -> List[User]:
        """Get all active users"""
        return self.user_repo.get_all_users()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information"""
        return self.user_repo.update_user(user_id, **kwargs)
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        return self.user_repo.deactivate_user(user_id)
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user and all associated data"""
        return self.user_repo.delete_user(user_id)
    
    def get_user_summary(self, user_id: int) -> Dict:
        """Get comprehensive user summary"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        # Get user's categories
        categories = self.category_repo.get_categories_by_user(user_id)
        
        # Get category mappings count
        category_mappings = self.category_repo.get_category_mappings_by_user(user_id)
        
        return {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'is_active': user.is_active,
            'categories_count': len(categories),
            'category_mappings_count': len(category_mappings),
            'categories': categories
        }
