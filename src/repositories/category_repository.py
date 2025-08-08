from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List, Dict
import logging

from src.models.database_models import CategoryMapping

logger = logging.getLogger(__name__)

class CategoryRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create_category_mapping(self, user_id: int, pattern: str, category: str, 
                              is_regex: bool = False, priority: int = 0) -> Optional[CategoryMapping]:
        """Create a new category mapping"""
        try:
            mapping = CategoryMapping(
                user_id=user_id,
                pattern=pattern,
                category=category,
                is_regex=is_regex,
                priority=priority
            )
            self.session.add(mapping)
            self.session.commit()
            self.session.refresh(mapping)
            logger.info(f"Created category mapping: {pattern} -> {category}")
            return mapping
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating category mapping: {str(e)}")
            return None
    
    def get_category_mappings_by_user(self, user_id: int) -> List[CategoryMapping]:
        """Get all category mappings for a user"""
        return self.session.query(CategoryMapping).filter(
            and_(
                CategoryMapping.user_id == user_id,
                CategoryMapping.is_active == True
            )
        ).order_by(desc(CategoryMapping.priority), CategoryMapping.pattern).all()
    
    def get_category_mapping_by_id(self, mapping_id: int) -> Optional[CategoryMapping]:
        """Get category mapping by ID"""
        return self.session.query(CategoryMapping).filter(CategoryMapping.id == mapping_id).first()
    
    def update_category_mapping(self, mapping_id: int, **kwargs) -> Optional[CategoryMapping]:
        """Update category mapping"""
        try:
            mapping = self.get_category_mapping_by_id(mapping_id)
            if not mapping:
                return None
            
            for key, value in kwargs.items():
                if hasattr(mapping, key):
                    setattr(mapping, key, value)
            
            self.session.commit()
            self.session.refresh(mapping)
            logger.info(f"Updated category mapping: {mapping_id}")
            return mapping
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating category mapping {mapping_id}: {str(e)}")
            return None
    
    def delete_category_mapping(self, mapping_id: int) -> bool:
        """Delete a category mapping"""
        try:
            mapping = self.get_category_mapping_by_id(mapping_id)
            if not mapping:
                return False
            
            self.session.delete(mapping)
            self.session.commit()
            logger.info(f"Deleted category mapping: {mapping_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting category mapping {mapping_id}: {str(e)}")
            return False
    
    def deactivate_category_mapping(self, mapping_id: int) -> bool:
        """Deactivate a category mapping instead of deleting"""
        try:
            mapping = self.get_category_mapping_by_id(mapping_id)
            if not mapping:
                return False
            
            mapping.is_active = False
            self.session.commit()
            logger.info(f"Deactivated category mapping: {mapping_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deactivating category mapping {mapping_id}: {str(e)}")
            return False
    
    def get_categories_by_user(self, user_id: int) -> List[str]:
        """Get list of unique categories used by a user"""
        mappings = self.get_category_mappings_by_user(user_id)
        categories = set()
        
        for mapping in mappings:
            categories.add(mapping.category)
        
        return sorted(list(categories))
    
    def categorize_transaction(self, user_id: int, description: str) -> Optional[str]:
        """
        Categorize a transaction using user's category mappings
        
        Args:
            user_id: User ID
            description: Transaction description
            
        Returns:
            Category name if found, None otherwise
        """
        mappings = self.get_category_mappings_by_user(user_id)
        
        # Sort by priority (higher priority first)
        mappings = sorted(mappings, key=lambda x: x.priority, reverse=True)
        
        description_lower = description.lower()
        
        for mapping in mappings:
            if mapping.is_regex:
                import re
                try:
                    if re.search(mapping.pattern, description_lower, re.IGNORECASE):
                        return mapping.category
                except re.error:
                    logger.warning(f"Invalid regex pattern: {mapping.pattern}")
                    continue
            else:
                # Simple string matching
                if mapping.pattern.lower() in description_lower:
                    return mapping.category
        
        return None
    
    def import_default_categories(self, user_id: int) -> List[CategoryMapping]:
        """Import default category mappings for a new user"""
        default_mappings = [
            # Food & Dining
            ('swiggy', 'food_dining', False, 10),
            ('zomato', 'food_dining', False, 10),
            ('restaurant', 'food_dining', False, 5),
            ('cafe', 'food_dining', False, 5),
            ('food', 'food_dining', False, 3),
            
            # Transport
            ('uber', 'transport', False, 10),
            ('ola', 'transport', False, 10),
            ('metro', 'transport', False, 8),
            ('railway', 'transport', False, 8),
            ('petrol', 'transport', False, 8),
            ('fuel', 'transport', False, 8),
            
            # Healthcare
            ('pharmacy', 'healthcare', False, 10),
            ('hospital', 'healthcare', False, 10),
            ('clinic', 'healthcare', False, 8),
            ('doctor', 'healthcare', False, 8),
            ('medical', 'healthcare', False, 5),
            
            # Shopping
            ('amazon', 'shopping', False, 10),
            ('flipkart', 'shopping', False, 10),
            ('myntra', 'shopping', False, 10),
            ('shop', 'shopping', False, 5),
            ('store', 'shopping', False, 5),
            
            # Subscriptions & Services
            ('netflix', 'subscriptions', False, 10),
            ('prime', 'subscriptions', False, 10),
            ('spotify', 'subscriptions', False, 10),
            ('subscription', 'subscriptions', False, 5),
            
            # Utilities
            ('electricity', 'utilities', False, 10),
            ('water', 'utilities', False, 10),
            ('gas', 'utilities', False, 10),
            ('internet', 'utilities', False, 10),
            ('mobile', 'utilities', False, 8),
            
            # Banking & Finance
            ('atm', 'banking', False, 10),
            ('neft', 'banking', False, 10),
            ('imps', 'banking', False, 10),
            ('upi', 'banking', False, 8),
            
            # Entertainment
            ('movie', 'entertainment', False, 10),
            ('cinema', 'entertainment', False, 10),
            ('theatre', 'entertainment', False, 8),
            ('game', 'entertainment', False, 5),
            
            # Travel
            ('hotel', 'travel', False, 10),
            ('flight', 'travel', False, 10),
            ('booking', 'travel', False, 8),
            ('trip', 'travel', False, 5),
            
            # Education
            ('course', 'education', False, 10),
            ('training', 'education', False, 10),
            ('book', 'education', False, 8),
            ('study', 'education', False, 5),
        ]
        
        created_mappings = []
        for pattern, category, is_regex, priority in default_mappings:
            mapping = self.create_category_mapping(user_id, pattern, category, is_regex, priority)
            if mapping:
                created_mappings.append(mapping)
        
        logger.info(f"Imported {len(created_mappings)} default category mappings for user {user_id}")
        return created_mappings
