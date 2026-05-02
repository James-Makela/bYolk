import re
import pandas as pd

from .models import Transaction

def generate_unique_hash(description, amount):
    receipt_number = re.findall(r"(?<=Receipt )\d{4,6}", description)
    stripped_amount = str(amount).replace(".", "_")
    if not receipt_number:
        return f"000000_{stripped_amount}"
    else:
        return f"{receipt_number[0]}_{stripped_amount}"

def process_description(description):
    description_string = f"{description}"
    if description_string == "":
        return "", "", ""
    description_pieces = description_string.split(" - ", 1)
    vendor = description_pieces[0]
    if len(description_pieces) >=2:
        second_split = description_pieces[1].rsplit(" - ", 1)
    else:
        second_split = []

    if len(second_split) == 2:
        purchase_type, receipt_details = second_split
    elif len(second_split) == 1:
        purchase_type = ""
        receipt_details = second_split[0]
    else:
        purchase_type = ""
        receipt_details = ""

    return vendor, purchase_type, receipt_details

def process_transaction_upload(user, csv_file):
    df = pd.read_csv(csv_file)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)

    transactions_to_create = []
    for _, row in df.iterrows():
        amount=row['Credit'] if pd.notnull(row.get('Credit')) else row.get('Debit', 0)
        hash = generate_unique_hash(row['Description'], amount)
        vendor, purchase_type, receipt_details = process_description(row['Description'])

        if not Transaction.objects.filter(unique_hash=hash).exists():
            transactions_to_create.append(
                Transaction(
                    user=user,
                    date=row['Date'].date(),
                    vendor=vendor,
                    purchase_type=purchase_type,
                    receipt_details=receipt_details,
                    amount=amount,
                    unique_hash=hash,
                )
            )

    return Transaction.objects.bulk_create(transactions_to_create)
