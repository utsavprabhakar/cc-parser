from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class TransactionType(enum.Enum):
    DEBIT = "Debit"
    CREDIT = "Credit"

class BankType(enum.Enum):
    AXIS_CREDIT = "Axis Credit Card"
    AXIS_SAVINGS = "Axis Savings"
    HDFC_CREDIT = "HDFC Credit Card"
    HDFC_SAVINGS = "HDFC Savings"
    ICICI_CREDIT = "ICICI Credit Card"
    ICICI_SAVINGS = "ICICI Savings"
    SBI_CREDIT = "SBI Credit Card"
    SBI_SAVINGS = "SBI Savings"
    OTHER = "Other"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    statements = relationship("Statement", back_populates="user")
    category_mappings = relationship("CategoryMapping", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class Statement(Base):
    __tablename__ = 'statements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    bank_type = Column(Enum(BankType), nullable=False)
    statement_date = Column(DateTime, nullable=False)
    opening_balance = Column(Float)
    closing_balance = Column(Float)
    total_debits = Column(Float, default=0.0)
    total_credits = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)
    parsing_status = Column(String(50), default='pending')  # pending, completed, failed
    parsing_errors = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="statements")
    transactions = relationship("Transaction", back_populates="statement")
    
    def __repr__(self):
        return f"<Statement(id={self.id}, file_name='{self.file_name}', bank_type={self.bank_type.value})>"

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey('statements.id'), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    category = Column(String(100))
    original_category = Column(String(100))  # Category before user correction
    is_categorized_by_llm = Column(Boolean, default=False)
    llm_confidence = Column(Float)  # Confidence score from LLM categorization
    user_corrected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    statement = relationship("Statement", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, category='{self.category}')>"

class CategoryMapping(Base):
    __tablename__ = 'category_mappings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    pattern = Column(String(255), nullable=False)  # Regex pattern or keyword
    category = Column(String(100), nullable=False)
    is_regex = Column(Boolean, default=False)
    priority = Column(Integer, default=0)  # Higher priority patterns are checked first
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="category_mappings")
    
    def __repr__(self):
        return f"<CategoryMapping(id={self.id}, pattern='{self.pattern}', category='{self.category}')>"
