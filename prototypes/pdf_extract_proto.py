from pypdf import PdfReader
import glob
import os
import string
import pandas as pd

path = "C:/Users/brand/Modern-Investment-Analytics-Platform/data/Personal Trades"
all_files = glob.glob(os.path.join(path, "TradeConfirmation*.pdf"))

transaction_start = ["You Bought", "You Sold"]
transaction_end = "Settlement Amount"

transactions = []

for file in all_files:

    reader = PdfReader(file)

    extracted_text = ""

    for page in reader.pages:
        extracted_text += page.extract_text()

    extracted_text_split = extracted_text.splitlines()
    extracted_text_split_strip = [s.strip() for s in extracted_text_split]

    current_transaction = []

    for line in extracted_text_split_strip:
        if line in transaction_start:
            if current_transaction:
                transactions.append(current_transaction)

            current_transaction = [line]
        elif current_transaction:

            current_transaction.append(line)

            if line.startswith(transaction_end):
                transactions.append(current_transaction)
                current_transaction = []

print(f"Found {len(transactions)} transactions\n")

#transactions = pd.DataFrame(transactions)

for i, transaction in enumerate(transactions, start=1):
    if transaction[0] == "You Bought":
        transaction_type = "BUY"
        #transactions['transaction_type'] == "BUY"
    elif transaction[0] == "You Sold":
        transaction_type = "SELL"
        #transactions['transaction_type'] == "SELL"

    quantity = transaction[1]

    strip_chars = "at" + string.whitespace

    price = transaction[2].strip(strip_chars)

    ticker = transaction[4]

    dates = transaction[5]

    trade_date = dates[:8]

    settlement_date = dates[9:17]

    print(f"transaction_type: {transaction_type}")
    #print(f"transaction_type: {transactions['transaction_type']}")
    print(f"quantity: {quantity}")
    print(f"price: {price}")
    print(f"ticker: {ticker}")
    print(f"trade_date: {trade_date}")
    print(f"settlement_date: {settlement_date}")
    print(transaction)
    print()