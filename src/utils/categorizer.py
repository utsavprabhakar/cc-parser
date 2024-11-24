from typing import Dict, List
import re

class TransactionCategorizer:
    def __init__(self):
        self.categories: Dict[str, List[str]] = {
            'food_dining': [
                r'swiggy', r'breads and banter', r'frothy tales', 
                r'maison du brownie', r'restaurant', r'cafe'
            ],
            'transport': [
                r'uber', r'ola', r'metro', r'railway', r'irctc'
            ],
            'travel': [
                r'ibibo', r'makemytrip', r'flight', r'ixigo'
            ],
            'shopping': [
                r'femina flaunt', r'retail', r'shop', r'store', r'market'
            ],
            'healthcare': [
                r'dr ', r'rxdx', r'hospital', r'pharmacy', r'clinic'
            ],
            'services': [
                r'urbanclap', r'cred', r'expressvpn'
            ],
            'donations': [
                r'earth saviours'
            ],
            'bank_transfer': [
                r'bbps payment', r'neft', r'imps', r'upi', r'transfer'
            ]
        }
    
    def categorize(self, description: str) -> str:
        """Categorize a transaction based on its description"""
        description = description.lower()
        
        for category, patterns in self.categories.items():
            if any(re.search(pattern, description, re.IGNORECASE) for pattern in patterns):
                return category
            
        return 'others'
    
    def add_category_pattern(self, category: str, pattern: str) -> None:
        """Add a new pattern to an existing or new category"""
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(pattern)