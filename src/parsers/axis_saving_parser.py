import pandas as pd
import pdfplumber
from datetime import datetime
from typing import List, Optional
import re

from src.models.transaction import Transaction
from src.utils.categorizer import TransactionCategorizer


class AxisSavingStatementParser:
    def __init__(self):
        self.categorizer = TransactionCategorizer()
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF statement"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() + '\n'
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            raise

    def parse_transaction_line(self, line: str) -> Optional[Transaction]:
        """Parse a single transaction line from the bank statement"""
        # Regular expression to match the transaction format from your example
        pattern = r'(\d{2}-\d{2}-\d{4})\s+(\/[^0-9]+)\s+(\d+\.\d{2})\s+(\d+\.\d{2})\s+(\d+)'
        
        match = re.search(pattern, line)
        
        if not match:
            return None
        
        try:
            date_str, description, debit_str, credit_str, balance_str = match.groups()
            
            # Parse date string like "31-10-2024" to datetime
            date = datetime.strptime(date_str, "%d-%m-%Y")
            
            # Process the description
            processed_description = self._process_description(description)
            
            # Determine transaction type and amount
            if debit_str:
                transaction_type = "Debit"
                amount = float(debit_str.replace(',', ''))
            elif credit_str:
                transaction_type = "Credit"
                amount = float(credit_str.replace(',', ''))
            else:
                return None  # Skip if no amount
            
            # Categorize the transaction
            category = self.categorizer.categorize(processed_description)
            
            return Transaction(
                date=date,
                description=processed_description,
                amount=amount,
                transaction_type=transaction_type,
                category=category
            )
            
        except (ValueError, IndexError) as e:
            print(f"Error parsing line: {line}")
            print(f"Error: {e}")
            return None

    def _process_description(self, description: str) -> str:
        """Process transaction description based on transaction type"""
        # For UPI transactions: extract value after 3rd / and before 4th /
        if "UPI" in description:
            parts = description.split('/')
            if len(parts) >= 4:
                return parts[3]  # Extract the entity name (4th part)
            return description
        
        # For other transactions, return as is
        return description
    
    def parse_statement(self, pdf_path: str) -> List[Transaction]:
        """Parse the entire statement and return list of transactions"""
        text = self.extract_text_from_pdf(pdf_path)
        transactions = []
        
        # Skip header lines and process transaction lines
        transaction_section = False
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Check for transaction section start
            if "OPENING BALANCE" in line:
                transaction_section = True
                continue
            
            # Check for transaction section end
            if "CLOSING BALANCE" in line:
                transaction_section = False
                continue
            
            # Process transaction lines
            if transaction_section and line and re.match(r'\d{2}-\d{2}-\d{4}', line):
                transaction = self.parse_transaction_line(line)
                if transaction:
                    transactions.append(transaction)
        
        return sorted(transactions, key=lambda x: x.date, reverse=True)
    
    def to_dataframe(self, transactions: List[Transaction]) -> pd.DataFrame:
        """Convert list of transactions to DataFrame"""
        if not transactions:
            return pd.DataFrame(columns=['date', 'description', 'amount', 'transaction_type', 'category'])
        
        # Convert transactions to dictionary format
        data = []
        for t in transactions:
            data.append({
                'date': t.date,
                'description': t.description,
                'amount': t.amount,
                'transaction_type': t.transaction_type,
                'category': t.category
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Sort by date
        df = df.sort_values('date', ascending=False)
        
        return df