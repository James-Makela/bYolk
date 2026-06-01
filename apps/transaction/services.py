import re
from datetime import datetime

import pandas as pd

from .models import Transaction


def generate_unique_hash(description, amount, balance, uid):
    receipt_number = re.findall(r"(?<=Receipt )\d{4,6}", description)
    stripped_amount = str(amount).replace(".", "_").strip("-")
    stripped_balance = str(balance).replace(".", "_").strip("-")
    if not receipt_number:
        return f"000000_{stripped_amount}{stripped_balance}{uid}"
    else:
        return f"{receipt_number[0]}_{stripped_amount}{uid}"


def process_description(description):
    description_string = f"{description}"
    if description_string == "":
        return "", "", ""
    description_pieces = description_string.split(" - ", 1)
    vendor = description_pieces[0].rstrip()
    if len(description_pieces) >= 2:
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


def get_actual_date(description):
    """
    Works out if there is a transaction date in the description,
    if so, this should be the transaction date, rather than the processed date.
    This helps us to keep track of spending when the money is spent rather than
    processed.
    """
    actual_date = re.findall(
        r"(\d+)[\s]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s]+(\d{4})",
        description,
    )
    if actual_date and len(actual_date[0]) == 3:
        try:
            date_string = " ".join(actual_date[0])
            return datetime.strptime(date_string, "%d %b %Y").date()
        except Exception:
            return None


def process_transaction_upload(user, csv_file):
    df = pd.read_csv(csv_file)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

    transactions_to_create = []
    for _, row in df.iterrows():
        amount = row["Credit"] if pd.notnull(row.get("Credit")) else row.get("Debit", 0)
        hash = generate_unique_hash(
            row["Description"], amount, row["Balance"], user.uid
        )
        vendor, purchase_type, receipt_details = process_description(row["Description"])
        date = get_actual_date(row["Description"])
        if not date:
            date = row["Date"].date()

        if (
            not Transaction.objects.filter(unique_hash=hash).exists()
            and "Internal" not in vendor
        ):
            transactions_to_create.append(
                Transaction(
                    user=user,
                    date=date,
                    vendor=vendor,
                    purchase_type=purchase_type,
                    receipt_details=receipt_details,
                    amount=amount,
                    unique_hash=hash,
                )
            )

    return Transaction.objects.bulk_create(transactions_to_create)
