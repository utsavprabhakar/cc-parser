class AxisBankStatementAnalyzer:
    """Analyzes parsed Axis Bank statement data"""
    
    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.df = self._create_dataframe()
    
    def _create_dataframe(self) -> pd.DataFrame:
        """Create DataFrame from transactions"""
        data = []
        for t in self.transactions:
            data.append({
                'date': t.date,
                'description': t.description,
                'amount': t.amount,
                'transaction_type': t.transaction_type,
                'category': t.category
            })
        
        df = pd.DataFrame(data)
        
        # Convert date strings to datetime objects if possible
        if not df.empty:
            try:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date', ascending=False)
            except:
                # If date conversion fails, keep as string
                pass
        
        return df
    
    def get_monthly_summary(self) -> pd.DataFrame:
        """Get monthly income and expense summary"""
        if self.df.empty:
            return pd.DataFrame()
        
        # Try to work with dates
        monthly = self.df.copy()
        
        # Extract month if date is datetime, otherwise try to parse it
        if pd.api.types.is_datetime64_any_dtype(monthly['date']):
            monthly['month'] = monthly['date'].dt.strftime('%Y-%m')
        else:
            # Try to extract month from date string
            try:
                monthly['month'] = monthly['date'].apply(
                    lambda x: datetime.strptime(x, "%d-%m-%Y").strftime('%Y-%m')
                )
            except:
                # If extraction fails, use the whole date as is
                monthly['month'] = monthly['date']
        
        # Group by month and transaction type
        debit_df = monthly[monthly['transaction_type'] == 'Debit']
        credit_df = monthly[monthly['transaction_type'] == 'Credit']
        
        # Calculate monthly totals
        debit_summary = debit_df.groupby('month')['amount'].sum().reset_index()
        credit_summary = credit_df.groupby('month')['amount'].sum().reset_index()
        
        # Merge summaries
        summary = pd.merge(debit_summary, credit_summary, on='month', how='outer', suffixes=('_debit', '_credit'))
        summary = summary.fillna(0)
        summary.columns = ['month', 'expenses', 'income']
        summary['net'] = summary['income'] - summary['expenses']
        
        return summary
    
    def get_category_summary(self) -> pd.DataFrame:
        """Get spending by category"""
        if self.df.empty:
            return pd.DataFrame()
        
        # Only consider debit transactions for category analysis
        debit_df = self.df[self.df['transaction_type'] == 'Debit'].copy()
        
        category_summary = debit_df.groupby('category').agg({
            'amount': 'sum'
        }).reset_index()
        
        category_summary = category_summary.sort_values('amount', ascending=False)
        
        return category_summary
    
    def get_largest_transactions(self, transaction_type='Debit', n=10) -> pd.DataFrame:
        """Get largest transactions of specified type"""
        if self.df.empty:
            return pd.DataFrame()
        
        filtered_df = self.df[self.df['transaction_type'] == transaction_type].copy()
        return filtered_df.sort_values('amount', ascending=False).head(n)
