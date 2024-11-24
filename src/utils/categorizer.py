from typing import Dict, List
import re

class TransactionCategorizer:
    def __init__(self):
        self.categories: Dict[str, List[str]] = {
            'food_dining': [
                r'swiggy', 
                r'maison du brownie',
                r'centro pmc',  # Restaurant
                r'secret story',  # Restaurant/Cafe
                r'maverick and farmer',  # Coffee shop
                r'zeptonow',  # Grocery/Food delivery
                r'bhola and blonde'  # Restaurant/Cafe
            ],
            'transport': [
                r'uber india',
                r'ola',
                r'metro',
                r'railway',
                r'irctc'
            ],
            'health_wellness': [
                r'monalisa pharma',
                r'dr ',
                r'hospital',
                r'clinic',
                r'rxdx',
                r'icici lombard',  # Health insurance
                r'torq 0 3 sports'  # Sports/Fitness
            ],
            'shopping': [
                r'mass enterprises',
                r'retail',
                r'shop',
                r'store',
                r'market'
            ],
            'subscriptions_services': [
                r'claude\.ai subscription',
                r'setupvpn\.com',
                r'urbanclap',
                r'cred'
            ],
            'donations_charity': [
                r'milaap social',
                r'earth saviours',
                r'donation'
            ],
            'bank_charges': [
                r'foreign currency transaction fee',
                r'gst',
                r'processing fee',
                r'annual fee'
            ],
            'payments_transfers': [
                r'bbps payment',
                r'neft',
                r'imps',
                r'upi',
                r'transfer',
                r'\d{6,}\s*\d*'  # Numeric reference numbers
            ],
            'insurance': [
                r'icici lombard general',
                r'insurance',
                r'policy'
            ],
            'home_utilities': [
                r'my gate',  # Society maintenance
                r'maintenance',
                r'electricity',
                r'water'
            ]
        }
    
    def categorize(self, description: str, amount: float = 0) -> str:
        """
        Categorize a transaction based on its description and amount
        
        Args:
            description (str): Transaction description
            amount (float): Transaction amount (optional)
            
        Returns:
            str: Category name
        """
        description = description.lower()
        
        # Check each category's patterns
        for category, patterns in self.categories.items():
            if any(re.search(pattern, description, re.IGNORECASE) for pattern in patterns):
                return category
                
        # If no match found in patterns, try to categorize based on amount and description
        # For transactions with numeric references
        if re.match(r'^\d+\s+\d*$', description.strip()):
            return 'payments_transfers'
            
        return 'others'
    
    def add_category_pattern(self, category: str, pattern: str) -> None:
        """
        Add a new pattern to an existing or new category
        
        Args:
            category (str): Category name
            pattern (str): Regex pattern to match
        """
        if category not in self.categories:
            self.categories[category] = []
        if pattern not in self.categories[category]:
            self.categories[category].append(pattern)
    
    def get_all_categories(self) -> List[str]:
        """
        Get list of all available categories
        
        Returns:
            List[str]: List of category names
        """
        return list(self.categories.keys())