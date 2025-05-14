import uuid
from decimal import Decimal
import datetime
#from pymongo import MongoClient # Import MongoClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Attempt to import ledger components
try:
    from .ledger import Ledger, Account, AccountType, JournalEntry, JournalEntryLine, JournalEntryLineType
except ImportError:
    from ledger import Ledger, Account, AccountType, JournalEntry, JournalEntryLine, JournalEntryLineType


class Product:
    def __init__(self, product_id, name, price, stock, cost_price=None):
        self.product_id = product_id
        self.name = name
        self.price = Decimal(str(price)) # Ensure Decimal
        self.stock = stock
        self.cost_price = Decimal(str(cost_price)) if cost_price is not None else Decimal('0.00')

    def __repr__(self):
        return f"Product(product_id='{self.product_id}', name='{self.name}', price={self.price}, stock={self.stock}, cost_price={self.cost_price})"
    def check_stock(self, quantity):
        """
        Check if the requested quantity is available in stock.
        """
        return self.stock >= quantity
    def update_stock(self, quantity):
        """
        Update the stock after an order is placed.
        """
        if self.check_stock(quantity):
            self.stock -= quantity
        else:
            raise ValueError(f"Not enough stock for product {self.product_id}. Available: {self.stock}, Requested: {quantity}")
# Example product instances (in a real application, these would be fetched from a database)


class Inventory:
    def __init__(self):
        self.products = {}

    def add_product(self, product):
        self.products[product.product_id] = product

    def get_product(self, product_id):
        return self.products.get(product_id)

    def check_stock(self, product_id, quantity):
        product = self.get_product(product_id)
        if product:
            return product.check_stock(quantity)
        return False

    def update_stock(self, product_id, quantity):
        product = self.get_product(product_id)
        if product:
            product.update_stock(quantity)
        else:
            raise ValueError(f"Product {product_id} not found in inventory.")
    
    def get_product_cost(self, product_id):
        product = self.get_product(product_id)
        if product:
            return product.cost_price
        return None # Return None if product or cost_price is not found

# Example inventory instance


class Order:
    def __init__(self, order_id, customer_id, items, customer_name=None, shipping_address=None, order_date=None):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = items 
        self.customer_name = customer_name
        self.shipping_address = shipping_address
        
        if isinstance(order_date, str):
            try:
                self.order_date = datetime.datetime.strptime(order_date, "%Y-%m-%d").date()
            except ValueError:
                self.order_date = datetime.date.today()
        elif isinstance(order_date, datetime.datetime): # Handle datetime objects
            self.order_date = order_date.date()
        elif isinstance(order_date, datetime.date):
            self.order_date = order_date
        else:
            self.order_date = datetime.date.today()

    def calculate_total(self):
        return sum(Decimal(str(item['quantity'])) * Decimal(str(item['unit_price'])) for item in self.items)

    def calculate_total_cost_of_goods_sold(self):
        return sum(Decimal(str(item['quantity'])) * Decimal(str(item.get('unit_cost', '0.00'))) for item in self.items)

    def to_dict(self):
        """Converts the Order object to a dictionary for MongoDB."""
        return {
            "_id": self.order_id, # Use order_id as MongoDB's _id
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "shipping_address": self.shipping_address,
            "order_date": datetime.datetime.combine(self.order_date, datetime.datetime.min.time()), # Store as BSON date
            "items": [{
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "unit_price": str(item["unit_price"]), # Store Decimal as string
                "unit_cost": str(item["unit_cost"])   # Store Decimal as string
            } for item in self.items],
            "total_amount": str(self.calculate_total()), # Store Decimal as string
            "total_cogs": str(self.calculate_total_cost_of_goods_sold()) # Store Decimal as string
        }

    def __repr__(self):
        return f"Order(order_id='{self.order_id}', customer_id='{self.customer_id}', items={len(self.items)}, total={self.calculate_total():.2f})"

def accept_purchase_order(order_data, inventory_system: Inventory, ledger_system: Ledger, dt_module: datetime, orders_collection=None):
    """
    Accepts a purchase order from an external customer.
    Args:
        order_data (dict): Purchase order details.
        inventory_system (Inventory): The inventory system instance.
        ledger_system (Ledger): The ledger system instance.
        dt_module (datetime): The datetime module.
        orders_collection (pymongo.collection.Collection, optional): MongoDB collection for orders.
    Returns:
        dict: Status of order processing.
    """
    print(f"Received purchase order: {order_data}")

    # Basic validation (can be expanded)
    required_fields = ['customer_id', 'items']
    if not all(key in order_data for key in required_fields):
        missing = [field for field in required_fields if field not in order_data]
        return {"status": "error", "message": f"Missing required order information: {', '.join(missing)}."}

    if not isinstance(order_data['items'], list) or not order_data['items']:
        return {"status": "error", "message": "Order must contain at least one item."}

    processed_items = []
    for item_index, item_data in enumerate(order_data['items']):
        required_item_fields = ['product_id', 'quantity', 'unit_price']
        if not all(key in item_data for key in required_item_fields):
            missing_item_fields = [field for field in required_item_fields if field not in item_data]
            return {"status": "error", "message": f"Invalid item data in order (item {item_index + 1}). Missing: {', '.join(missing_item_fields)}."}
        
        product_id = item_data['product_id']
        quantity = item_data['quantity']
        unit_price = Decimal(str(item_data['unit_price']))

        if not isinstance(quantity, int) or quantity <= 0:
            return {"status": "error", "message": f"Item quantity for '{product_id}' must be a positive integer."}
        if unit_price < Decimal('0.00'):
            return {"status": "error", "message": f"Item unit price for '{product_id}' must be a non-negative number."}

        # Get product cost from inventory
        unit_cost = inventory_system.get_product_cost(product_id)
        if unit_cost is None: # Product might not exist or cost not set
             print(f"Warning: Cost price for product {product_id} not found. COGS will be 0 for this item.")
             unit_cost = Decimal('0.00')

        processed_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'unit_cost': unit_cost
        })

    # 1. Generate a unique order ID
    order_id = str(uuid.uuid4())
    
    # Ensure order_date is a date object before passing to Order constructor
    order_date_input = order_data.get('order_date')
    if isinstance(order_date_input, str):
        try:
            current_order_date = dt_module.datetime.strptime(order_date_input, "%Y-%m-%d").date()
        except ValueError:
            current_order_date = dt_module.date.today()
    elif isinstance(order_date_input, dt_module.datetime):
        current_order_date = order_date_input.date()
    elif isinstance(order_date_input, dt_module.date):
        current_order_date = order_date_input
    else:
        current_order_date = dt_module.date.today()


    # Create an Order object
    new_order = Order(
        order_id=order_id,
        customer_id=order_data['customer_id'],
        items=processed_items, 
        customer_name=order_data.get('customer_name'),
        shipping_address=order_data.get('shipping_address'),
        order_date=current_order_date
    )

    # 2. Check product availability and update inventory
    for item in new_order.items:
        product_id = item['product_id']
        quantity = item['quantity']
        if not inventory_system.check_stock(product_id, quantity):
            return {"status": "error", "message": f"Insufficient stock for product {product_id}."}
    
    # If all checks pass, update stock (ideally in a transaction)
    for item in new_order.items:
        inventory_system.update_stock(item['product_id'], item['quantity'])
    print(f"Inventory updated for order {new_order.order_id}")


    # 3. Calculate total order amount and COGS
    total_amount = new_order.calculate_total()
    total_cogs = new_order.calculate_total_cost_of_goods_sold()


    # 4. Process payment (placeholder)
    payment_successful = True 
    if not payment_successful:
        # Rollback inventory changes if payment fails
        for item in new_order.items:
            inventory_system.update_stock(item['product_id'], -item['quantity']) # Add back
        return {"status": "error", "message": "Payment processing failed."}
    print(f"Payment processing placeholder for order {new_order.order_id}")

    # 5. Save the order to your database (MongoDB if collection is provided)
    if orders_collection is not None: # <--- Corrected line
        try:
            order_dict = new_order.to_dict()
            orders_collection.insert_one(order_dict)
            print(f"Order {new_order.order_id} saved to MongoDB.")
        except Exception as e:
            print(f"Error saving order {new_order.order_id} to MongoDB: {e}")
            # Potentially rollback previous steps or flag for manual review
            return {"status": "error", "message": f"Failed to save order to database: {e}"}
    else:
        print(f"Order {new_order.order_id} processed (DB save skipped as no collection provided).")
    
    # 6. Create and Record Journal Entry
    try:
        transaction_date = new_order.order_date # This is already a date object
        entry_description = f"Sale for order {new_order.order_id}"
        sale_entry = JournalEntry(transaction_date, entry_description)

        # Assuming cash sale for now. Could be Accounts Receivable.
        cash_account = ledger_system.get_account("Cash") 
        sales_revenue_account = ledger_system.get_account("Sales Revenue")
        
        # Debit Cash, Credit Sales Revenue
        sale_entry.add_line(cash_account, total_amount, JournalEntryLineType.DEBIT)
        sale_entry.add_line(sales_revenue_account, total_amount, JournalEntryLineType.CREDIT)

        # Record COGS if applicable
        if total_cogs > Decimal('0.00'):
            cogs_account = ledger_system.get_account("Cost of Goods Sold")
            inventory_asset_account = ledger_system.get_account("Inventory") # Assuming 'Inventory' is the asset account name
            sale_entry.add_line(cogs_account, total_cogs, JournalEntryLineType.DEBIT)
            sale_entry.add_line(inventory_asset_account, total_cogs, JournalEntryLineType.CREDIT)

        if not sale_entry.is_balanced():
            # This should ideally not happen if logic is correct
            return {"status": "error", "message": "Internal error: Journal entry for sale is not balanced."}

        ledger_system.record_entry(sale_entry)
        print(f"Journal entry recorded for order {new_order.order_id}")

    except ValueError as e: # Catch errors like account not found
        # Potentially rollback other actions or log critical error
        print(f"Critical error recording journal entry: {e}")
        return {"status": "error", "message": f"Failed to record financial transaction: {e}"}


    # 7. Send order confirmation (placeholder)
    print(f"Order confirmation email placeholder for order {new_order.order_id}")


    print(f"Purchase order for customer {new_order.customer_id} processed successfully. Order: {new_order}")
    return {
        "status": "success",
        "message": "Purchase order accepted.",
        "order_id": new_order.order_id,
        "total_amount": float(total_amount) # Convert Decimal to float for JSON if needed
    }

# Example usage (you would call this from your API endpoint):
if __name__ == '__main__':
    # --- Setup MongoDB ---
    mylogin = input(f'Please enter the login : ')
    mypassword = input(f'Please enter the password : ')
    
    mongo_client = None
    db_orders_collection = None
    db_ledger_collection = None  # Add a collection for ledger data
    uri = f"mongodb+srv://{mylogin}:{mypassword}@josecluster.wjr8n1f.mongodb.net/?retryWrites=true&w=majority&appName=JOSECLUSTER"
    
    try:
        # Correct way to instantiate MongoClient with an SRV URI
        mongo_client = MongoClient(uri, server_api=ServerApi('1'))
        mongo_client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        db = mongo_client['onlinestore'] 
        db_orders_collection = db['orders']
        db_ledger_collection = db['ledger']  # Create a collection for ledger data
        print(f"Successfully connected to MongoDB Atlas database: {db.name}.")
    except Exception as e:
        print(f"Could not connect to MongoDB Atlas: {e}. Orders and ledger data will not be saved to DB.")

    # --- Setup Inventory ---
    inventory = Inventory()
    product1 = Product(product_id="prod_abc", name="Laptop", price=Decimal('1200.00'), stock=20, cost_price=Decimal('800.00')) # Increased stock
    product2 = Product(product_id="prod_xyz", name="Mouse", price=Decimal('25.00'), stock=100, cost_price=Decimal('10.00')) # Increased stock
    inventory.add_product(product1)
    inventory.add_product(product2)

    # --- Setup Ledger ---
    main_ledger = Ledger()
    # Assets
    main_ledger.add_account(Account("Cash", AccountType.ASSET, Decimal('25000'))) # Increased initial cash
    main_ledger.add_account(Account("Accounts Receivable", AccountType.ASSET))
    initial_inventory_value = sum(p.cost_price * p.stock for p in inventory.products.values())
    main_ledger.add_account(Account("Inventory", AccountType.ASSET, initial_inventory_value))
    # Liabilities
    main_ledger.add_account(Account("Accounts Payable", AccountType.LIABILITY))
    # Equity
    initial_owners_capital = Decimal('25000') + initial_inventory_value
    main_ledger.add_account(Account("Owner's Capital", AccountType.EQUITY, initial_owners_capital))
    main_ledger.add_account(Account("Retained Earnings", AccountType.EQUITY))
    # Income
    main_ledger.add_account(Account("Sales Revenue", AccountType.INCOME))
    # Expenses
    main_ledger.add_account(Account("Cost of Goods Sold", AccountType.EXPENSE))
    
    print("--- Initial Ledger Account Balances ---")
    for acc_name, acc in main_ledger.accounts.items():
        print(acc)
    print("--- Initial Inventory ---")
    for prod_id, prod in inventory.products.items():
        print(prod)


    sample_order_1 = {
        "customer_id": "cust_7890",
        "customer_name": "Jane Doe",
        "shipping_address": "123 Main St, Anytown, USA",
        "order_date": "2025-05-14", 
        "items": [
            {"product_id": "prod_abc1", "quantity": 1, "unit_price": 1200.00},
            {"product_id": "prod_xyz1", "quantity": 2, "unit_price": 25.00}
        ]
    }
    print("\n--- Processing Order 1 ---")
    result1 = accept_purchase_order(sample_order_1, inventory, main_ledger, datetime, db_orders_collection)
    print(f"Order 1 Result: {result1}")

    sample_order_2 = {
        "customer_id": "cust_1236",
        "customer_name": "John Smith",
        "order_date": datetime.datetime(2025, 5, 15, 10, 30, 0), # Example with datetime object
        "items": [
            {"product_id": "prod_xyz", "quantity": 5, "unit_price": 24.50} 
        ]
    }
    print("\n--- Processing Order 2 ---")
    result2 = accept_purchase_order(sample_order_2, inventory, main_ledger, datetime, db_orders_collection)
    print(f"Order 2 Result: {result2}")

    # --- Save Ledger Data to MongoDB ---
    if db_ledger_collection is not None:
        try:
            # Save journal entries
            journal_entries = [entry.to_dict() for entry in main_ledger.journal_entries]
            if journal_entries:
                db_ledger_collection.insert_many(journal_entries)
                print(f"Saved {len(journal_entries)} journal entries to the 'ledger' collection.")

            # Save chart of accounts
            chart_of_accounts = [account.to_dict() for account in main_ledger.accounts.values()]
            if chart_of_accounts:
                db_ledger_collection.insert_many(chart_of_accounts)
                print(f"Saved {len(chart_of_accounts)} accounts to the 'ledger' collection.")
        except Exception as e:
            print(f"Error saving ledger data to MongoDB: {e}")
    else:
        print("Ledger data was not saved because the MongoDB collection was not initialized.")

    # Close MongoDB connection when done
    if mongo_client:
        mongo_client.close()
        print("\nMongoDB connection closed.")

























