from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Transaction:
    date: datetime
    description: str
    amount: float
    transaction_type: str  # 'Debit' or 'Credit'
    category: Optional[str] = None
    
    @property
    def is_debit(self) -> bool:
        return self.transaction_type.lower() == 'debit'
    
    @property
    def is_credit(self) -> bool:
        return self.transaction_type.lower() == 'credit'