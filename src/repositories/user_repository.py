from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
import logging

from src.models.database_models import User

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create_user(self, username: str, email: str) -> Optional[User]:
        """Create a new user"""
        try:
            user = User(username=username, email=email)
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            logger.info(f"Created user: {username}")
            return user
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Failed to create user {username}: {str(e)}")
            return None
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating user {username}: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.session.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.session.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.session.query(User).filter(User.email == email).first()
    
    def get_all_users(self) -> List[User]:
        """Get all active users"""
        return self.session.query(User).filter(User.is_active == True).all()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            self.session.commit()
            self.session.refresh(user)
            logger.info(f"Updated user: {user.username}")
            return user
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return None
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.is_active = False
            self.session.commit()
            logger.info(f"Deactivated user: {user.username}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deactivating user {user_id}: {str(e)}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user (cascade will handle related records)"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            self.session.delete(user)
            self.session.commit()
            logger.info(f"Deleted user: {user.username}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return False
