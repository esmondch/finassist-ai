
import sqlite3
import random
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent / "data" / "transactions.db"

# All transaction records are fictional and created for this academic prototype.

ORIGINAL_TRANSACTIONS = [
    ("TXN1001", "CUST001", "2026-10-20 09:15:00", "ABC Supermarket", 42.80, "SGD", "COMPLETED", "GROCERIES"),
    ("TXN1002", "CUST001", "2026-10-20 12:30:00", "City Cafe", 8.50, "SGD", "COMPLETED", "DINING"),
    ("TXN1003", "CUST001", "2026-10-21 14:10:00", "Online Store", 129.90, "SGD", "PENDING", "SHOPPING"),
    ("TXN1004", "CUST001", "2026-10-22 08:45:00", "Metro Transport", 2.20, "SGD", "COMPLETED", "TRANSPORT"),
    ("TXN1005", "CUST001", "2026-10-22 16:20:00", "Electronics Shop", 399.00, "SGD", "REFUNDED", "SHOPPING"),
    ("TXN1006", "CUST001", "2026-10-23 11:05:00", "Utility Services", 86.40, "SGD", "COMPLETED", "BILLS"),

    ("TXN2001", "CUST002", "2026-10-20 10:05:00", "Fresh Mart", 31.20, "SGD", "COMPLETED", "GROCERIES"),
    ("TXN2002", "CUST002", "2026-10-21 13:45:00", "Online Books", 24.90, "SGD", "COMPLETED", "SHOPPING"),
    ("TXN2003", "CUST002", "2026-10-22 17:30:00", "Example Transfer", 150.00, "SGD", "FAILED", "TRANSFER"),
    ("TXN2004", "CUST002", "2026-10-23 09:20:00", "Coffee Corner", 6.80, "SGD", "PENDING", "DINING"),

    ("TXN3001", "CUST003", "2026-10-20 08:30:00", "Metro Transport", 1.90, "SGD", "COMPLETED", "TRANSPORT"),
    ("TXN3002", "CUST003", "2026-10-21 15:15:00", "Fashion Outlet", 78.00, "SGD", "COMPLETED", "SHOPPING"),
    ("TXN3003", "CUST003", "2026-10-22 19:10:00", "Example Transfer", 250.00, "SGD", "PENDING", "TRANSFER"),
]


# Merchant, currency, minimum amount, maximum amount.
# Amounts are denominated in the transaction's own currency.
TRANSACTION_TYPES = {
    "GROCERIES": [
        ("FairPrice", "SGD", 8, 180),
        ("Sheng Siong", "SGD", 6, 120),
        ("Giant Supermarket", "SGD", 10, 160),
        ("Cold Storage", "SGD", 15, 200),
    ],
    "DINING": [
        ("Toast Box", "SGD", 4, 35),
        ("Food Republic", "SGD", 6, 45),
        ("McDonald's", "SGD", 5, 30),
        ("Local Restaurant", "SGD", 12, 100),
    ],
    "SHOPPING": [
        ("Popular Bookstore", "SGD", 8, 100),
        ("Shopee", "SGD", 5, 300),
        ("Lazada", "SGD", 10, 400),
        ("Uniqlo", "SGD", 20, 250),
        ("Overseas Online Store", "USD", 10, 200),
        ("Malaysia Retail Store", "MYR", 20, 500),
    ],
    "TRANSPORT": [
        ("Grab", "SGD", 5, 65),
        ("ComfortDelGro", "SGD", 8, 55),
        ("SimplyGo", "SGD", 1, 15),
    ],
    "BILLS": [
        ("SP Services", "SGD", 35, 300),
        ("StarHub", "SGD", 25, 120),
        ("Singtel", "SGD", 25, 150),
    ],
    "SUBSCRIPTIONS": [
        ("Netflix", "SGD", 10, 30),
        ("Spotify", "SGD", 5, 20),
    ],
    "TRANSFER": [
        ("Local Bank Transfer", "SGD", 20, 2000),
        ("Overseas Remittance", "USD", 50, 1500),
        ("Malaysia Remittance", "MYR", 50, 2000),
    ],
    "TRAVEL": [
        ("Hotel Booking", "SGD", 80, 900),
        ("Airline Booking", "SGD", 100, 1200),
        ("Overseas Hotel", "EUR", 50, 600),
        ("Overseas Travel Booking", "USD", 30, 800),
    ],
}

# Status probabilities vary by transaction category.
STATUS_OPTIONS = {
    "GROCERIES": (["COMPLETED", "PENDING", "FAILED"], [94, 4, 2]),
    "DINING": (["COMPLETED", "PENDING", "FAILED"], [93, 5, 2]),
    "SHOPPING": (
        ["COMPLETED", "PENDING", "FAILED", "REFUNDED"],
        [78, 10, 3, 9]
    ),
    "TRANSPORT": (["COMPLETED", "PENDING", "FAILED"], [94, 4, 2]),
    "BILLS": (["COMPLETED", "PENDING", "FAILED"], [90, 7, 3]),
    "SUBSCRIPTIONS": (["COMPLETED", "PENDING", "FAILED"], [94, 4, 2]),
    "TRANSFER": (["COMPLETED", "PENDING", "FAILED"], [82, 10, 8]),
    "TRAVEL": (
        ["COMPLETED", "PENDING", "FAILED", "REFUNDED"],
        [75, 12, 3, 10]
    ),
}


def generate_additional_transactions():
    """Generate 87 reproducible synthetic transactions."""
    rng = random.Random(20261103)

    transactions = []
    categories = list(TRANSACTION_TYPES.keys())

    start_date = datetime(2026, 10, 24)

    for i in range(87):
        transaction_id = f"TXN{4001 + i}"
        customer_id = f"CUST{(i % 10) + 1:03d}"

        category = rng.choice(categories)

        merchant, currency, min_amount, max_amount = rng.choice(
            TRANSACTION_TYPES[category]
        )

        amount = round(rng.uniform(min_amount, max_amount), 2)

        possible_statuses, weights = STATUS_OPTIONS[category]
        status = rng.choices(
            possible_statuses,
            weights=weights,
            k=1
        )[0]

        transaction_date = start_date + timedelta(
            days=rng.randint(0, 9),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59)
        )

        transactions.append((
            transaction_id,
            customer_id,
            transaction_date.strftime("%Y-%m-%d %H:%M:%S"),
            merchant,
            amount,
            currency,
            status,
            category
        ))

    return transactions


GENERATED_TRANSACTIONS = generate_additional_transactions()


def initialise_database():
    """Create the transaction table and populate the demo records."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                merchant TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                category TEXT NOT NULL
            )
        """)

        # Preserve the original 13 records.
        connection.executemany("""
            INSERT OR IGNORE INTO transactions (
                transaction_id, customer_id, transaction_date,
                merchant, amount, currency, status, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ORIGINAL_TRANSACTIONS)

        # Update generated records when the script is rerun.
        # This replaces the earlier mathematically generated versions
        # without deleting the original 13 transactions.
        connection.executemany("""
            INSERT INTO transactions (
                transaction_id, customer_id, transaction_date,
                merchant, amount, currency, status, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(transaction_id) DO UPDATE SET
                customer_id = excluded.customer_id,
                transaction_date = excluded.transaction_date,
                merchant = excluded.merchant,
                amount = excluded.amount,
                currency = excluded.currency,
                status = excluded.status,
                category = excluded.category
        """, GENERATED_TRANSACTIONS)

        total = connection.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        customer_counts = connection.execute("""
            SELECT customer_id, COUNT(*)
            FROM transactions
            GROUP BY customer_id
            ORDER BY customer_id
        """).fetchall()

        status_counts = connection.execute("""
            SELECT status, COUNT(*)
            FROM transactions
            GROUP BY status
            ORDER BY status
        """).fetchall()

        category_counts = connection.execute("""
            SELECT category, COUNT(*)
            FROM transactions
            GROUP BY category
            ORDER BY category
        """).fetchall()

        currency_counts = connection.execute("""
            SELECT currency, COUNT(*)
            FROM transactions
            GROUP BY currency
            ORDER BY currency
        """).fetchall()

    print(f"Database ready: {DB_PATH}")
    print(f"Original records: {len(ORIGINAL_TRANSACTIONS)}")
    print(f"Generated records: {len(GENERATED_TRANSACTIONS)}")
    print(f"Total records in database: {total}")

    print("\nTransactions by customer:")
    for customer_id, count in customer_counts:
        print(f"  {customer_id}: {count}")

    print("\nTransactions by status:")
    for status, count in status_counts:
        print(f"  {status}: {count}")

    print("\nTransactions by category:")
    for category, count in category_counts:
        print(f"  {category}: {count}")

    print("\nTransactions by currency:")
    for currency, count in currency_counts:
        print(f"  {currency}: {count}")


def lookup_transaction(transaction_id, customer_id):
    """Look up one transaction belonging to the selected demo customer."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        result = connection.execute("""
            SELECT transaction_id, transaction_date, merchant,
                   amount, currency, status, category
            FROM transactions
            WHERE transaction_id = ?
              AND customer_id = ?
        """, (
            transaction_id.strip().upper(),
            customer_id.strip().upper()
        )).fetchone()

    return dict(result) if result else None


def get_customer_transactions(customer_id, status=None, limit=10):
    """Return recent transactions for one demo customer."""
    customer_id = customer_id.strip().upper()
    limit = max(1, min(int(limit), 50))

    query = """
        SELECT transaction_id, transaction_date, merchant,
               amount, currency, status, category
        FROM transactions
        WHERE customer_id = ?
    """
    params = [customer_id]

    if status:
        query += " AND status = ?"
        params.append(status.strip().upper())

    query += " ORDER BY transaction_date DESC LIMIT ?"
    params.append(limit)

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        results = connection.execute(query, params).fetchall()

    return [dict(row) for row in results]


if __name__ == "__main__":
    initialise_database()

    print("\nTest original transaction:")
    print(lookup_transaction("TXN1001", "CUST001"))

    print("\nTest generated transaction:")
    print(lookup_transaction("TXN4001", "CUST001"))

    print("\nTest customer transaction history:")
    for transaction in get_customer_transactions("CUST001"):
        print(transaction)

    print("\nTest pending transactions:")
    for transaction in get_customer_transactions(
        "CUST001", status="PENDING"
    ):
        print(transaction)

    print("\nTest customer isolation:")
    print(lookup_transaction("TXN1001", "CUST002"))
