import sys
from src.main import analyze_statement

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run.py <path-to-pdf>")
        sys.exit(1)
    
    analyze_statement(sys.argv[1])