import sys
import copy
import datetime
from typing import List, Dict, Any
from decimal import Decimal
from collections import defaultdict
from enum import Enum
from decimal import Decimal
from typing import List, Dict, Any
import datetime # Ensure datetimoure is imported
import uuid # For generating unique IDs for journal entries in DB
import datetime # For BSON date conversion


class BalanceSheet:
    def __init__(self):
        self.assets = {}
        self.liabilities = {}
        self.equity = {}
        self.income = {}
        self.expense = {}

    def add_asset(self, name, amount):
        # Ensure amount is Decimal, or convert if necessary
        current_amount = self.assets.get(name, Decimal('0.00'))
        if not isinstance(current_amount, Decimal):
            current_amount = Decimal(str(current_amount))
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        self.assets[name] = current_amount + amount

    def add_liability(self, name, amount):
        # Ensure amount is Decimal, or convert if necessary
        current_amount = self.liabilities.get(name, Decimal('0.00'))
        if not isinstance(current_amount, Decimal):
            current_amount = Decimal(str(current_amount))
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        self.liabilities[name] = current_amount + amount

    def add_equity(self, name, amount):
        # Ensure amount is Decimal, or convert if necessary
        current_amount = self.equity.get(name, Decimal('0.00'))
        if not isinstance(current_amount, Decimal):
            current_amount = Decimal(str(current_amount))
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        self.equity[name] = current_amount + amount

    def apply_net_income(self, amount: Decimal, equity_account_name: str = "Retained Earnings"):
        """
        Applies net income to an equity account (typically Retained Earnings).
        Net income increases equity.
        """
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if amount < Decimal('0.00'):
            raise ValueError("Net income amount must be non-negative.")
        self.add_equity(equity_account_name, amount)

    def apply_net_loss(self, amount: Decimal, equity_account_name: str = "Retained Earnings"):
        """
        Applies net loss to an equity account (typically Retained Earnings).
        Net loss decreases equity. The loss amount should be positive.
        """
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if amount < Decimal('0.00'):
            raise ValueError("Net loss amount must be non-negative.")
        self.add_equity(equity_account_name, -amount) # Net loss reduces equity

    def get_balance(self):
        total_assets = sum(Decimal(str(v)) for v in self.assets.values())
        total_liabilities = sum(Decimal(str(v)) for v in self.liabilities.values())
        total_equity = sum(Decimal(str(v)) for v in self.equity.values())
        return {
            "assets": total_assets,
            "liabilities": total_liabilities,
            "equity": total_equity,
        }
    def __repr__(self):
        return f"BalanceSheet(assets={self.assets}, liabilities={self.liabilities}, equity={self.equity})"
    def __str__(self):
        return f"Balance Sheet:\nAssets: {self.assets}\nLiabilities: {self.liabilities}\nEquity: {self.equity}"
    def __getitem__(self, key):
        if key == "assets":
            return self.assets
        elif key == "liabilities":
            return self.liabilities
        elif key == "equity":
            return self.equity
        else:
            raise KeyError(f"Invalid key: {key}")
    def __setitem__(self, key, value):
        if key == "assets":
            if not isinstance(value, dict) or not all(isinstance(v, (int, float, Decimal)) for v in value.values()):
                raise ValueError("Assets must be a dictionary with numeric values.")
            self.assets = {k: Decimal(str(v)) for k, v in value.items()}
        elif key == "liabilities":
            if not isinstance(value, dict) or not all(isinstance(v, (int, float, Decimal)) for v in value.values()):
                raise ValueError("Liabilities must be a dictionary with numeric values.")
            self.liabilities = {k: Decimal(str(v)) for k, v in value.items()}
        elif key == "equity":
            if not isinstance(value, dict) or not all(isinstance(v, (int, float, Decimal)) for v in value.values()):
                raise ValueError("Equity must be a dictionary with numeric values.")
            self.equity = {k: Decimal(str(v)) for k, v in value.items()}
        else:
            raise KeyError(f"Invalid key: {key}")
    def __delitem__(self, key):
        if key == "assets":
            del self.assets
        elif key == "liabilities":
            del self.liabilities
        elif key == "equity":
            del self.equity
        else:
            raise KeyError(f"Invalid key: {key}")
    def __contains__(self, key):
        return key in self.assets or key in self.liabilities or key in self.equity
    def __len__(self):
        return len(self.assets) + len(self.liabilities) + len(self.equity)
    def __iter__(self):
        return iter(self.assets.items()) + iter(self.liabilities.items()) + iter(self.equity.items())
    def __next__(self):
        if not self.assets and not self.liabilities and not self.equity:
            raise StopIteration
        for key, value in self.assets.items():
            yield key, value
        for key, value in self.liabilities.items():
            yield key, value
        for key, value in self.equity.items():
            yield key, value
    def __reversed__(self):
        for key, value in reversed(self.assets.items()):
            yield key, value
        for key, value in reversed(self.liabilities.items()):
            yield key, value
        for key, value in reversed(self.equity.items()):
            yield key, value
    def __hash__(self):
        return hash((frozenset(self.assets.items()), frozenset(self.liabilities.items()), frozenset(self.equity.items())))
    def __eq__(self, other):
        if not isinstance(other, BalanceSheet):
            return False
        return (self.assets == other.assets and
                self.liabilities == other.liabilities and
                self.equity == other.equity)
    def __ne__(self, other):
        return not self.__eq__(other)
    def __lt__(self, other):
        if not isinstance(other, BalanceSheet):
            return NotImplemented
        return (self.assets < other.assets or
                self.liabilities < other.liabilities or
                self.equity < other.equity)
    def __le__(self, other):
        if not isinstance(other, BalanceSheet):
            return NotImplemented
        return (self.assets <= other.assets and
                self.liabilities <= other.liabilities and
                self.equity <= other.equity)
    def __gt__(self, other):
        if not isinstance(other, BalanceSheet):
            return NotImplemented
        return (self.assets > other.assets or
                self.liabilities > other.liabilities or
                self.equity > other.equity)
    def __ge__(self, other):
        if not isinstance(other, BalanceSheet):
            return NotImplemented
        return (self.assets >= other.assets and
                self.liabilities >= other.liabilities and
                self.equity >= other.equity)
    def __bool__(self):
        return bool(self.assets or self.liabilities or self.equity)
    def __call__(self):
        return self.get_balance()
    def __format__(self, format_spec):
        return f"Balance Sheet:\nAssets: {self.assets}\nLiabilities: {self.liabilities}\nEquity: {self.equity}"
    def __sizeof__(self):
        return sum(sys.getsizeof(v) for v in self.assets.values()) + \
               sum(sys.getsizeof(v) for v in self.liabilities.values()) + \
               sum(sys.getsizeof(v) for v in self.equity.values())
    def __copy__(self):
        new_balance_sheet = BalanceSheet()
        new_balance_sheet.assets = self.assets.copy()
        new_balance_sheet.liabilities = self.liabilities.copy()
        new_balance_sheet.equity = self.equity.copy()
        return new_balance_sheet
    def __deepcopy__(self, memo):
        new_balance_sheet = BalanceSheet()
        new_balance_sheet.assets = copy.deepcopy(self.assets, memo)
        new_balance_sheet.liabilities = copy.deepcopy(self.liabilities, memo)
        new_balance_sheet.equity = copy.deepcopy(self.equity, memo)
        return new_balance_sheet
    
class IncomeStatement:
    def __init__(self):
        self.revenue = {}
        self.expenses = {}

    def add_revenue(self, name, amount):
        if name in self.revenue:
            self.revenue[name] += amount
        else:
            self.revenue[name] = amount

    def add_expense(self, name, amount):
        if name in self.expenses:
            self.expenses[name] += amount
        else:
            self.expenses[name] = amount

    def get_net_income(self):
        total_revenue = sum(self.revenue.values())
        total_expenses = sum(self.expenses.values())
        return total_revenue - total_expenses

    def __repr__(self):
        return f"IncomeStatement(revenue={self.revenue}, expenses={self.expenses})"
    
class CashFlowStatement:
    def __init__(self):
        self.operating_activities = {}
        self.investing_activities = {}
        self.financing_activities = {}

    def add_operating_activity(self, name, amount):
        if name in self.operating_activities:
            self.operating_activities[name] += amount
        else:
            self.operating_activities[name] = amount

    def add_investing_activity(self, name, amount):
        if name in self.investing_activities:
            self.investing_activities[name] += amount
        else:
            self.investing_activities[name] = amount

    def add_financing_activity(self, name, amount):
        if name in self.financing_activities:
            self.financing_activities[name] += amount
        else:
            self.financing_activities[name] = amount

    def get_net_cash_flow(self):
        total_operating = sum(self.operating_activities.values())
        total_investing = sum(self.investing_activities.values())
        total_financing = sum(self.financing_activities.values())
        return total_operating + total_investing + total_financing

    def __repr__(self):
        return f"CashFlowStatement(operating={self.operating_activities}, investing={self.investing_activities}, financing={self.financing_activities})"
    
class AccountType(Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    EXPENSE = "Expense"

class JournalEntryLineType(Enum):
    DEBIT = "Debit"
    CREDIT = "Credit"

class Account:
    def __init__(self, name: str, account_type: AccountType, initial_balance: Decimal = Decimal('0.00')):
        if not isinstance(account_type, AccountType):
            raise ValueError("account_type must be an instance of AccountType Enum.")
        self.name = name
        self.account_type = account_type
        self.balance = Decimal(str(initial_balance))

    def _apply_transaction(self, amount: Decimal, is_debit: bool):
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if amount < Decimal('0.00'):
            raise ValueError("Transaction amount must be non-negative.")

        if self.account_type == AccountType.ASSET:
            self.balance += amount if is_debit else -amount
        elif self.account_type == AccountType.LIABILITY:
            self.balance += -amount if is_debit else amount
        elif self.account_type == AccountType.EQUITY:
            self.balance += -amount if is_debit else amount
        elif self.account_type == AccountType.INCOME: 
            self.balance += -amount if is_debit else amount
        elif self.account_type == AccountType.EXPENSE: 
            self.balance += amount if is_debit else -amount
        else:
            raise ValueError(f"Unknown account type: {self.account_type}")


    def credit(self, amount: Decimal):
        self._apply_transaction(amount, is_debit=False)

    def debit(self, amount: Decimal):
        self._apply_transaction(amount, is_debit=True)

    def to_dict(self):
        """Converts the Account object to a dictionary for MongoDB."""
        return {
            # Using name as _id assumes account names are unique and will be used for upserting
            "_id": self.name, 
            "name": self.name,
            "account_type": self.account_type.value,
            "balance": str(self.balance) # Store Decimal as string
        }

    def __repr__(self):
        return f"Account(name='{self.name}', type='{self.account_type.value}', balance={self.balance:.2f})"

    def __str__(self):
        return f"{self.name} ({self.account_type.value}): {self.balance:.2f}"

class JournalEntryLine:
    def __init__(self, account: Account, amount: Decimal, entry_type: JournalEntryLineType):
        if not isinstance(account, Account):
            raise ValueError("account must be an instance of Account.")
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if amount <= Decimal('0.00'): 
            raise ValueError("Journal entry line amount must be positive.")
        if not isinstance(entry_type, JournalEntryLineType):
            raise ValueError("entry_type must be an instance of JournalEntryLineType.")

        self.account = account
        self.amount = amount
        self.entry_type = entry_type

    def __repr__(self):
        return f"JournalEntryLine(account='{self.account.name}', amount={self.amount:.2f}, type='{self.entry_type.value}')"


class JournalEntry:
    def __init__(self, date: datetime.date, description: str, lines: List[JournalEntryLine] = None):
        if not isinstance(date, datetime.date):
            raise ValueError("Date must be a datetime.date object.")
        self.date = date
        self.description = description
        self.lines: List[JournalEntryLine] = lines if lines is not None else []
        self.entry_id = str(uuid.uuid4()) # Give each journal entry a unique ID

    def add_line(self, account: Account, amount: Decimal, entry_type: JournalEntryLineType):
        self.lines.append(JournalEntryLine(account, amount, entry_type))

    def is_balanced(self) -> bool:
        total_debits = sum(line.amount for line in self.lines if line.entry_type == JournalEntryLineType.DEBIT)
        total_credits = sum(line.amount for line in self.lines if line.entry_type == JournalEntryLineType.CREDIT)
        return total_debits == total_credits

    def to_dict(self):
        """Converts the JournalEntry object to a dictionary for MongoDB."""
        return {
            "_id": self.entry_id, # Use the pre-generated UUID
            "date": datetime.datetime.combine(self.date, datetime.datetime.min.time()), # Store as BSON date
            "description": self.description,
            "lines": [
                {
                    "account_name": line.account.name, # Store account name for reference
                    "amount": str(line.amount), # Store Decimal as string
                    "entry_type": line.entry_type.value # "Debit" or "Credit"
                } for line in self.lines
            ],
            "is_balanced": self.is_balanced()
        }

    def __repr__(self):
        return f"JournalEntry(id={self.entry_id}, date={self.date}, description='{self.description}', lines={len(self.lines)}, balanced={self.is_balanced()})"


class Ledger:
    def __init__(self):
        self.accounts: Dict[str, Account] = {} 
        self.journal_entries: List[JournalEntry] = []

    def add_account(self, account: Account):
        if account.name in self.accounts:
            raise ValueError(f"Account with name '{account.name}' already exists.")
        self.accounts[account.name] = account

    def get_account(self, name: str) -> Account:
        account = self.accounts.get(name)
        if not account:
            raise ValueError(f"Account with name '{name}' not found.")
        return account

    def record_entry(self, entry: JournalEntry):
        if not entry.is_balanced():
            raise ValueError("Journal entry must be balanced (total debits must equal total credits).")
        
        for line in entry.lines:
            account_to_update = line.account
            if line.entry_type == JournalEntryLineType.DEBIT:
                account_to_update.debit(line.amount)
            elif line.entry_type == JournalEntryLineType.CREDIT:
                account_to_update.credit(line.amount)
        
        self.journal_entries.append(entry)
        # print(f"Recorded Journal Entry: {entry.description} on {entry.date}") # Optional

    def save_journal_entries_to_db(self, journal_entries_collection):
        """Saves all current journal entries to the specified MongoDB collection."""
        if journal_entries_collection is not None and self.journal_entries:
            entries_to_insert = [entry.to_dict() for entry in self.journal_entries]
            if entries_to_insert:
                try:
                    journal_entries_collection.insert_many(entries_to_insert, ordered=False) # ordered=False allows partial success
                    print(f"Attempted to save {len(entries_to_insert)} journal entries to MongoDB.")
                    # Consider clearing self.journal_entries here if they should only be saved once per run
                    # self.journal_entries = [] 
                except Exception as e: # Catch pymongo.errors.BulkWriteError for more details if needed
                    print(f"Error saving journal entries to MongoDB: {e}")
        elif not self.journal_entries:
            print("No journal entries to save.")

    def save_chart_of_accounts_to_db(self, accounts_collection):
        """Saves/Updates the current chart of accounts to the specified MongoDB collection."""
        if accounts_collection is not None and self.accounts:
            from pymongo import UpdateOne # Import here to keep it local to the method
            operations = []
            for account_name, account_obj in self.accounts.items():
                account_dict = account_obj.to_dict()
                # Use account_name (which is _id in account_dict) for upserting
                operations.append(
                    UpdateOne({"_id": account_name}, {"$set": account_dict}, upsert=True)
                )
            if operations:
                try:
                    result = accounts_collection.bulk_write(operations, ordered=False)
                    print(f"Chart of Accounts: {result.upserted_count} upserted, {result.modified_count} modified in MongoDB.")
                except Exception as e: # Catch pymongo.errors.BulkWriteError
                    print(f"Error saving chart of accounts to MongoDB: {e}")
        elif not self.accounts:
            print("No accounts in the chart to save.")
    
    # ... (generate_balance_sheet, generate_income_statement, __repr__) ...
    def __repr__(self):
        return f"Ledger(accounts={len(self.accounts)}, entries={len(self.journal_entries)})"

    
if __name__ == "__main__":
    # Example usage for testing Ledger components in isolation
    
    # --- BalanceSheet Example ---
    balance_sheet = BalanceSheet()
    balance_sheet.add_asset("Cash", Decimal('10000'))
    balance_sheet.add_liability("Loan", Decimal('5000'))
    balance_sheet.add_equity("Owner's Capital", Decimal('5000'))
    print("--- BalanceSheet Example ---")
    print(balance_sheet)
    print("Initial Total Balance:", balance_sheet.get_balance())
    net_income_for_period = Decimal('1500.00')
    balance_sheet.apply_net_income(net_income_for_period)
    print("\nAfter recognizing net income:")
    print(balance_sheet)
    print("Total Balance:", balance_sheet.get_balance())

    # --- Account Examples ---
    print("\n--- Account Examples ---")
    try:
        cash_account = Account("Cash on Hand", AccountType.ASSET, Decimal('1500.75'))
        print(cash_account)
        cash_account.debit(Decimal('200.25'))
        print(f"After debit: {cash_account}")
        
        accounts_payable = Account("Supplier Invoices", AccountType.LIABILITY, Decimal('3000'))
        print(accounts_payable)
        accounts_payable.credit(Decimal('500'))
        print(f"After credit: {accounts_payable}")
    except ValueError as e:
        print(f"Error creating or updating account: {e}")

    # --- Ledger Example (without MongoDB for isolated testing) ---
    print("\n--- Ledger Example (Isolated Test) ---")
    isolated_ledger = Ledger()
    try:
        # Add accounts to ledger
        test_cash = Account("Test Cash", AccountType.ASSET, Decimal('1000'))
        test_revenue = Account("Test Revenue", AccountType.INCOME)
        isolated_ledger.add_account(test_cash)
        isolated_ledger.add_account(test_revenue)

        # Create a journal entry
        entry_date = datetime.date.today() # Ensure datetime is imported
        journal_entry = JournalEntry(date=entry_date, description="Test Sale")
        journal_entry.add_line(test_cash, Decimal('500.00'), JournalEntryLineType.DEBIT)
        journal_entry.add_line(test_revenue, Decimal('500.00'), JournalEntryLineType.CREDIT)

        isolated_ledger.record_entry(journal_entry)

        print("Ledger after recording journal entry:")
        for acc_name, account_obj in isolated_ledger.accounts.items():
            print(account_obj)
        print(f"Total journal entries recorded: {len(isolated_ledger.journal_entries)}")
        if isolated_ledger.journal_entries:
            print(f"First journal entry: {isolated_ledger.journal_entries[0]}")

    except ValueError as e:
        print(f"Error in ledger operations: {e}")

    # The MongoDB connection and saving logic, and the integration with Inventory/Orders,
    # should primarily be tested from orders.py or a dedicated integration test script.
    print("\nNote: MongoDB and Order processing examples are in orders.py")