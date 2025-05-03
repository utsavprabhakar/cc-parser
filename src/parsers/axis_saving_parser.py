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
        """Parse a single transaction line from the Axis Bank statement"""
        # Regular expression to match Axis Bank statement transaction line
        pattern = r'(\d{2}-\d{2}-\d{4})\s+(.*?)(?:\s+(\d+\.\d{2}))?\s+(\d+\.\d{2})\s+\d+$'
        
        match = re.match(pattern, line)
        
        if match:
            date_str, description, amount_str, balance_str = match.groups()
            
            try:
                date = datetime.strptime(date_str, "%d-%m-%Y")
                
                # Determine if it's a debit or credit transaction
                is_debit = True
                # Check if it contains credit indicators
                if "CR-" in description or "SALARY" in description.upper():
                    is_debit = False
                
                # Clean amount
                amount = float(amount_str.replace(',', '')) if amount_str else 0.0
                
                # Set transaction type based on debit/credit
                transaction_type = "Debit" if is_debit else "Credit"
                
                # Categorize the transaction
                category = self.categorizer.categorize(description)
                
                # Create and return Transaction object using your existing model
                return Transaction(
                    date=date_str,  # Using original date string format
                    description=description.strip(),
                    amount=amount,
                    transaction_type=transaction_type,
                    category=category
                )
                
            except ValueError as e:
                print(f"Error parsing line: {line}")
                print(f"Error: {e}")
                return None
        return None
    
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