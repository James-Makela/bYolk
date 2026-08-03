import re
from datetime import datetime

import pandas as pd
import pymupdf

from .models import Transaction


# Functions for ING .csv
def generate_unique_hash(description, amount, balance, uid, receipt_number=None):
    if not receipt_number:
        receipt_number = re.findall(r"(?<=Receipt )\d{4,6}", description)[0]
    stripped_amount = str(amount).replace(".", "_").strip("-")
    stripped_balance = str(balance).replace(".", "_").strip("-")
    if not receipt_number:
        return f"000000_{stripped_amount}{stripped_balance}{uid}"
    else:
        return f"{receipt_number}_{stripped_amount}{uid}"


def process_description_ing(description):
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


def process_transaction_upload_ing(user, csv_file):
    df = pd.read_csv(csv_file)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

    transactions_to_create = []

    # Duplicate tracking to ignore corrections and reversals
    seen_unique_hash = set()
    duplicates = []

    for _, row in df.iterrows():
        amount = row["Credit"] if pd.notnull(row.get("Credit")) else row.get("Debit", 0)
        hash = generate_unique_hash(
            row["Description"], amount, row["Balance"], user.uid
        )
        vendor, purchase_type, receipt_details = process_description_ing(
            row["Description"]
        )
        vendor, purchase_type, receipt_details = process_description_ing(
            row["Description"]
        )
        date = get_actual_date(row["Description"])
        if not date:
            date = row["Date"].date()

        if hash in seen_unique_hash:
            duplicates.append(hash)
        else:
            seen_unique_hash.add(hash)

        if (
            not Transaction.objects.filter(unique_hash=hash).exists()
            and "Internal" not in vendor
            and purchase_type != "Internal"
            and hash not in duplicates
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


# Functions for ANZ+ pdf
def get_amount(parts, gap):
    prefix = "-" if gap < 15 else ""
    amount_string = f'{prefix}{parts[2].strip("$").replace(",", "")}'
    return amount_string


def get_date(parts, year):
    if parts[-1].startswith("Effective"):
        date = datetime.strptime(parts[-1].split()[-1], "%d/%m/%Y").date()
    else:
        datestring = f"{parts[0]} {year}"
        date = datetime.strptime(datestring, "%d %b %Y").date()
    return date


def get_description(parts):
    if len(parts) > 4 and "Effective Date" not in parts[4]:
        description = f"{parts[1]} {parts[4]}"
    else:
        description = parts[1]
    return description


def get_receipt_number(description):
    receipt_number = re.findall(r"#\d{6}", description)
    if len(receipt_number) > 0:
        receipt_number = receipt_number[0].strip("#")
    else:
        receipt_number = None
    return receipt_number


def get_transaction_type(description):
    transaction_types = [
        "Visa Debit",
        "Pay/Salary",
        "Payment",
        "Eftpos",
        "Pension/Superannuation",
    ]
    transaction_type = None
    for tx_type in transaction_types:
        if tx_type.lower() in description.lower():
            transaction_type = tx_type
    return transaction_type


def get_vendor(transaction_type, description, amount):
    match transaction_type:
        case "Visa Debit":
            vendor = re.sub(r"VISA DEBIT PURCHASE CARD \d{4} ", "", description)
        case "Pay/Salary":
            vendor = description.replace("PAY/SALARY FROM ", "")
        case "Payment":
            replace_string = "PAYMENT TO " if amount[0] == "-" else "PAYMENT FROM "
            vendor = description.replace(replace_string, "")
        case "Eftpos":
            vendor = description.replace("EFTPOS ", "")
        case "Pension/Superannuation":
            vendor = description.replace("PENSION/SUPERANNUATION FROM ", "")
        case _:
            vendor = description

    vendor = re.sub(r" #*[A-Za-z]*\d+\S*\d*$", "", vendor)
    return vendor


def process_transaction_upload_anzplus(user, document):
    transactions_to_create = []
    year = document.get_page_text(0).split("\n")[1].split()[-1]

    # Duplicate tracking to ignore corrections and reversals
    seen_unique_hash = set()
    duplicates = []

    for page in document:
        sf = page.search_for("Date")

        ry0 = sf[0].y1
        rx0 = page.rect.x0
        ry1 = page.rect.y1 - 60
        rx1 = page.rect.x1

        # Clipped rectangle object
        cr = pymupdf.Rect(rx0, ry0, rx1, ry1)

        lines = page.get_text(clip=cr, sort=True).split("\n\n\n")
        for line in lines:
            # If we hit a line starting with Opening - wwe have reached the end
            if line.strip().startswith("Opening"):
                break

            # Ignore transfers and round ups
            if "ROUND UP" in line or "TRANSFER FROM" in line or "TRANSFER TO" in line:
                continue

            space_count = line.split("$")[1].count(" ")
            parts = [" ".join(string.split()) for string in re.split(r"\s{2,}", line)]

            amount = get_amount(parts, space_count)
            date = get_date(parts, year)
            description = get_description(parts)
            receipt_number = get_receipt_number(description)
            purchase_type = get_transaction_type(description)
            vendor = get_vendor(purchase_type, description, amount)
            balance = parts[3]
            hash = generate_unique_hash(
                description, amount, balance, user.uid, receipt_number
            )

            if hash in seen_unique_hash:
                duplicates.append(hash)
            else:
                seen_unique_hash.add(hash)

            if (
                not Transaction.objects.filter(unique_hash=hash).exists()
                and "Internal" not in vendor
                and purchase_type != "Internal"
                and hash not in duplicates
            ):
                transactions_to_create.append(
                    Transaction(
                        user=user,
                        date=date,
                        vendor=vendor,
                        purchase_type=purchase_type,
                        receipt_details=description,
                        amount=amount,
                        unique_hash=hash,
                    )
                )

    return Transaction.objects.bulk_create(transactions_to_create)
