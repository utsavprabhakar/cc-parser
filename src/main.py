import sys
from pathlib import Path
import os
import pandas as pd
from datetime import datetime

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers.axis_parser import AxisBankStatementParser

def analyze_statement(pdf_path: str) -> None:
    parser = AxisBankStatementParser()
    
    try:
        print(f"\nAnalyzing statement: {pdf_path}")
        
        # Parse transactions
        print("Parsing transactions...")
        transactions = parser.parse_statement(pdf_path)
        
        if not transactions:
            print("No transactions found in the statement.")
            return
            
        print(f"Found {len(transactions)} transactions")
        
        # Convert to DataFrame for analysis
        print("Converting to DataFrame...")
        df = parser.to_dataframe(transactions)
        
        # Basic analysis
        total_debits = df[df['transaction_type'] == 'Debit']['amount'].sum()
        total_credits = df[df['transaction_type'] == 'Credit']['amount'].sum()
        
        # Category-wise spending - Fixed aggregation
        debit_mask = df['transaction_type'] == 'Debit'
        category_totals = df[debit_mask].groupby('category')['amount'].sum().round(2)
        category_counts = df[debit_mask].groupby('category').size()
        
        # Combine the results into a single DataFrame
        category_spending = pd.DataFrame({
            'Total': category_totals,
            'Count': category_counts
        })
        
        # Print summary
        print("\n=== Statement Analysis ===")
        # print(f"Statement Date: {df['date'].max().strftime('%d %b %Y')}")
        print(f"\nTotal Spending: ₹{total_debits:,.2f}")
        print(f"Total Credits: ₹{total_credits:,.2f}")
        print(f"\nTransactions by Category:")
        print(category_spending)
        
        # Save to Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(pdf_path).parent / f"statement_analysis_{timestamp}.xlsx"
        
        # Create Excel writer with multiple sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Transactions sheet
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Summary sheet - ensure index is written
            category_spending.to_excel(writer, sheet_name='Category Summary', index=True)
            
            # Add additional summary sheet
            summary_data = {
                'Metric': ['Total Debits', 'Total Credits', 'Net Flow', 'Transaction Count'],
                'Value': [
                    f'₹{total_debits:,.2f}',
                    f'₹{total_credits:,.2f}',
                    f'₹{(total_credits - total_debits):,.2f}',
                    len(df)
                ]
            }
            pd.DataFrame(summary_data).to_excel(
                writer, 
                sheet_name='Overall Summary',
                index=False
            )
            
        print(f"\nDetailed analysis saved to: {output_path}")
        
    except Exception as e:
        print(f"\nError analyzing statement: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/main.py <path-to-pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
        
    analyze_statement(pdf_path)