import pandas as pd
import pdfplumber
from datetime import datetime
from typing import List, Optional
import re

from src.models.transaction import Transaction
from src.utils.categorizer import TransactionCategorizer

class AxisBankStatementParser:
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
        """Parse a single transaction line from the statement"""
        pattern = r'(\d{2}\s+[A-Za-z]+\s+\'\d{2})\s+(.*?)\s+₹\s*([\d,]+\.\d{2})\s+(Debit|Credit)'
        match = re.match(pattern, line)
        
        if match:
            date_str, description, amount, txn_type = match.groups()
            try:
                # date = datetime.strptime(date_str, "%d %b '%y")
                amount_clean = float(amount.replace(',', ''))

                # print(self.categorizer.categorize(description))
                
                return Transaction(
                    date=date_str,
                    description=description.strip(),
                    amount=amount_clean,
                    transaction_type=txn_type,
                    category=self.categorizer.categorize(description)
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
        
        for line in text.split('\n'):
            # Skip header and footer lines
            if ('Transaction Details' in line or 
                'Page' in line or 
                'Credit Card Number' in line or 
                'End of Transaction' in line or
                not line.strip()):
                continue
                
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