# Credit Card Statement Analyser - Phase 1

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python application to analyze bank statements with database-backed storage and enhanced categorization.

## 🚀 Phase 1 Features

- **Database-Backed Storage**: SQLite database for persistent data storage
- **Multi-User Support**: User management with individual category mappings
- **Enhanced Categorization**: User-specific category rules with priority system
- **Statement Management**: Track multiple statements per user
- **Advanced Analytics**: Spending analysis, monthly comparisons, and trends
- **CLI Interface**: Command-line tool for easy interaction
- **Backward Compatibility**: Still supports the original PDF parsing functionality

## 📋 Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## ⚡️ Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/username/cc-parser.git
cd cc-parser

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Initialize the database (creates cc_parser.db in project root)
python cli.py init-db
```

### 3. Create a User

```bash
# Create a new user with default category mappings
python cli.py create-user john_doe john@example.com
```

### 4. Process Statements

```bash
# Process a statement for a user
python cli.py process data/statements/AXISMB_24-11-2024.pdf john_doe
```

### 5. View Analysis

```bash
# View overall spending analysis
python cli.py analyze john_doe

# Compare spending between months
python cli.py analyze john_doe --month1 2024-11 --month2 2024-10

# List user's categories
python cli.py categories john_doe
```

## 🏗️ Architecture

### Database Schema

- **Users**: User management with email and username
- **Statements**: Statement metadata and processing status
- **Transactions**: Individual transaction records with categorization
- **CategoryMappings**: User-specific category rules and patterns

### Service Layer

- **UserService**: User management operations
- **StatementService**: Statement processing and management
- **TransactionService**: Transaction analysis and categorization

### Repository Pattern

- **UserRepository**: Database operations for users
- **StatementRepository**: Database operations for statements
- **TransactionRepository**: Database operations for transactions
- **CategoryRepository**: Database operations for category mappings

## 📊 CLI Commands

### Database Management
```bash
python cli.py init-db                    # Initialize database
```

### User Management
```bash
python cli.py create-user <username> <email>  # Create new user
python cli.py list-users                       # List all users
```

### Statement Processing
```bash
python cli.py process <pdf_path> <username>    # Process statement
```

### Analysis
```bash
python cli.py analyze <username>                    # Overall analysis
python cli.py analyze <username> --month1 2024-11 --month2 2024-10  # Monthly comparison
python cli.py categories <username>                # List categories
```

## 🔧 Configuration

### Database Configuration

The application uses SQLite by default, creating `cc_parser.db` in the project root. For production, you can configure a different database:

```python
from src.database.database import DatabaseManager

# Use PostgreSQL
db_manager = DatabaseManager("postgresql://user:pass@localhost/cc_parser")
db_manager.initialize()
```

### Category Mappings

Users get default category mappings on creation, including:
- **Food & Dining**: swiggy, zomato, restaurant, cafe
- **Transport**: uber, ola, metro, petrol, fuel
- **Healthcare**: pharmacy, hospital, clinic, doctor
- **Shopping**: amazon, flipkart, myntra, shop
- **Subscriptions**: netflix, prime, spotify
- **Utilities**: electricity, water, gas, internet
- **Banking**: atm, neft, imps, upi
- **Entertainment**: movie, cinema, theatre
- **Travel**: hotel, flight, booking
- **Education**: course, training, book

## 📈 Analysis Features

### Spending Analysis
- Total spending and transaction counts
- Category-wise breakdown
- Average transaction amounts
- Top spending categories

### Monthly Comparisons
- Month-over-month spending changes
- Percentage change calculations
- Category-wise comparisons

### User-Specific Features
- Individual category mappings
- Learning from user corrections
- Priority-based categorization

## 🔄 Backward Compatibility

The original functionality is still available:

```bash
# Original command still works
python run.py data/statements/AXISMB_24-11-2024.pdf
```

## 🧪 Testing

```bash
# TODO: Add test commands
python -m pytest tests/
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚧 Roadmap

### Phase 2: LLM Integration
- Universal PDF parser using LLMs
- Intelligent transaction categorization
- Natural language querying

### Phase 3: Advanced Analytics
- Spending pattern analysis
- Budget tracking and alerts
- Financial insights and recommendations

### Phase 4: Conversational Interface
- Chat interface for financial queries
- Voice input/output capabilities
- Proactive insights and alerts

## 🙏 Acknowledgments

- Claude <3
- SQLAlchemy for database management
- pandas for data analysis