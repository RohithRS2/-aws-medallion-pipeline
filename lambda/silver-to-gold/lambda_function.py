import boto3
import csv
import io
import urllib.parse
from collections import defaultdict

s3 = boto3.client("s3")


def lambda_handler(event, context):

    # Get S3 event information
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"]
    )

    print(f"Reading Silver file: s3://{bucket}/{key}")

    # Read Silver file
    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    content = response["Body"].read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(content))

    # Find columns from the Silver file
    fieldnames = reader.fieldnames

    print(f"Columns found: {fieldnames}")

    # Detect category column
    category_column = None

    for column in fieldnames:
        if column.lower() in [
            "category",
            "product_category",
            "transaction_category",
            "type"
        ]:
            category_column = column
            break

    # Detect amount column
    amount_column = None

    for column in fieldnames:
        if column.lower() in [
            "amount",
            "transaction_amount",
            "total_amount",
            "price",
            "value"
        ]:
            amount_column = column
            break

    if not category_column:
        raise Exception("Category column not found")

    if not amount_column:
        raise Exception("Amount column not found")

    print(f"Category column: {category_column}")
    print(f"Amount column: {amount_column}")

    # Aggregate data
    summary = defaultdict(
        lambda: {
            "transaction_count": 0,
            "total_amount": 0.0
        }
    )

    rows_processed = 0

    for row in reader:

        category = row.get(category_column, "").strip()

        try:
            amount = float(
                row.get(amount_column, "0").strip()
            )
        except (ValueError, AttributeError):
            continue

        if not category:
            category = "Unknown"

        summary[category]["transaction_count"] += 1
        summary[category]["total_amount"] += amount

        rows_processed += 1

    # Create Gold output
    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "category",
        "transaction_count",
        "total_amount"
    ])

    for category, data in summary.items():

        writer.writerow([
            category,
            data["transaction_count"],
            round(data["total_amount"], 2)
        ])

    # Gold file
    gold_key = "gold/gold_transactions.csv"

    print(f"Uploading Gold file to: s3://{bucket}/{gold_key}")

    s3.put_object(
        Bucket=bucket,
        Key=gold_key,
        Body=output.getvalue().encode("utf-8"),
        ContentType="text/csv"
    )

    print(
        f"Gold file created: s3://{bucket}/{gold_key}"
    )

    return {
        "statusCode": 200,
        "message": "Silver to Gold transformation completed",
        "source": f"s3://{bucket}/{key}",
        "destination": f"s3://{bucket}/{gold_key}",
        "rows_processed": rows_processed,
        "categories_created": len(summary)
    }
