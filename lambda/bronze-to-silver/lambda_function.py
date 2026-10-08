import boto3
import csv
import os
import tempfile
import urllib.parse

s3 = boto3.client("s3")


def lambda_handler(event, context):

    # =========================================================
    # 1. GET S3 BUCKET AND OBJECT FROM S3 EVENT
    # =========================================================

    bucket = event["Records"][0]["s3"]["bucket"]["name"]

    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"]
    )

    print(f"Reading Bronze file: s3://{bucket}/{key}")


    # =========================================================
    # 2. DOWNLOAD BRONZE FILE TO TEMP STORAGE
    # =========================================================

    input_file = "/tmp/bronze_transactions.csv"
    output_file = "/tmp/clean_transactions.csv"

    print("Downloading Bronze file...")

    s3.download_file(
        bucket,
        key,
        input_file
    )

    print("Bronze file downloaded.")


    # =========================================================
    # 3. COUNTERS
    # =========================================================

    rows_processed = 0
    rows_written = 0
    duplicates_removed = 0
    invalid_rows_removed = 0
    outliers_removed = 0

    seen_transaction_ids = set()


    # =========================================================
    # 4. READ BRONZE AND CREATE SILVER
    # =========================================================

    with open(
        input_file,
        "r",
        encoding="utf-8",
        newline=""
    ) as infile, open(
        output_file,
        "w",
        encoding="utf-8",
        newline=""
    ) as outfile:

        reader = csv.DictReader(infile)

        # Check required columns
        required_columns = [
            "transaction_id",
            "customer_id",
            "product_category",
            "quantity",
            "unit_price",
            "transaction_date"
        ]

        if not reader.fieldnames:

            raise Exception(
                "Bronze CSV does not contain headers."
            )

        missing_columns = [
            column
            for column in required_columns
            if column not in reader.fieldnames
        ]

        if missing_columns:

            raise Exception(
                f"Missing required columns: "
                f"{missing_columns}"
            )


        # Silver columns
        fieldnames = [
            "transaction_id",
            "customer_id",
            "product_category",
            "quantity",
            "unit_price",
            "transaction_date",
            "transaction_amount"
        ]


        writer = csv.DictWriter(
            outfile,
            fieldnames=fieldnames
        )

        writer.writeheader()


        # =====================================================
        # 5. PROCESS EACH TRANSACTION
        # =====================================================

        for row in reader:

            rows_processed += 1


            # -------------------------------------------------
            # CLEAN BASIC VALUES
            # -------------------------------------------------

            transaction_id = (
                str(row["transaction_id"]).strip()
            )

            customer_id = (
                str(row["customer_id"]).strip()
            )

            product_category = (
                str(row["product_category"]).strip().title()
            )

            quantity_value = (
                str(row["quantity"]).strip()
            )

            unit_price_value = (
                str(row["unit_price"]).strip()
            )

            transaction_date = (
                str(row["transaction_date"]).strip()
            )


            # -------------------------------------------------
            # REMOVE EMPTY TRANSACTIONS
            # -------------------------------------------------

            if not transaction_id:

                invalid_rows_removed += 1
                continue


            if not customer_id:

                invalid_rows_removed += 1
                continue


            if not product_category:

                invalid_rows_removed += 1
                continue


            if not quantity_value:

                invalid_rows_removed += 1
                continue


            if not unit_price_value:

                invalid_rows_removed += 1
                continue


            if not transaction_date:

                invalid_rows_removed += 1
                continue


            # -------------------------------------------------
            # REMOVE DUPLICATE TRANSACTION IDs
            # -------------------------------------------------

            if transaction_id in seen_transaction_ids:

                duplicates_removed += 1
                continue

            seen_transaction_ids.add(transaction_id)


            # -------------------------------------------------
            # VALIDATE QUANTITY
            # -------------------------------------------------

            try:

                quantity = int(quantity_value)

            except ValueError:

                invalid_rows_removed += 1
                continue


            if quantity <= 0:

                invalid_rows_removed += 1
                continue


            # -------------------------------------------------
            # VALIDATE UNIT PRICE
            # -------------------------------------------------

            try:

                unit_price = float(unit_price_value)

            except ValueError:

                invalid_rows_removed += 1
                continue


            if unit_price <= 0:

                invalid_rows_removed += 1
                continue


            # -------------------------------------------------
            # REMOVE EXTREME PRICE OUTLIER
            # -------------------------------------------------

            if unit_price >= 99999:

                outliers_removed += 1
                continue


            # -------------------------------------------------
            # STANDARDIZE DATE
            # -------------------------------------------------

            try:

                date_part = transaction_date[:10]

                year, month, day = date_part.split("-")

                transaction_date_clean = (
                    f"{year}-{month}-{day}"
                )

            except Exception:

                invalid_rows_removed += 1
                continue


            # -------------------------------------------------
            # CALCULATE TRANSACTION AMOUNT
            # -------------------------------------------------

            transaction_amount = round(
                quantity * unit_price,
                2
            )


            # -------------------------------------------------
            # CREATE CLEAN SILVER RECORD
            # -------------------------------------------------

            clean_row = {

                "transaction_id":
                    transaction_id,

                "customer_id":
                    customer_id,

                "product_category":
                    product_category,

                "quantity":
                    quantity,

                "unit_price":
                    f"{unit_price:.2f}",

                "transaction_date":
                    transaction_date_clean,

                "transaction_amount":
                    f"{transaction_amount:.2f}"
            }


            writer.writerow(clean_row)

            rows_written += 1


            # -------------------------------------------------
            # PROGRESS LOG
            # -------------------------------------------------

            if rows_processed % 100000 == 0:

                print(
                    f"Processed: {rows_processed:,} | "
                    f"Clean rows: {rows_written:,} | "
                    f"Duplicates removed: "
                    f"{duplicates_removed:,} | "
                    f"Outliers removed: "
                    f"{outliers_removed:,}"
                )


    # =========================================================
    # 6. UPLOAD CLEAN SILVER FILE
    # =========================================================

    silver_key = "silver/clean_transactions.csv"

    print(
        f"Uploading Silver file: "
        f"s3://{bucket}/{silver_key}"
    )

    s3.upload_file(
        output_file,
        bucket,
        silver_key,
        ExtraArgs={
            "ContentType": "text/csv"
        }
    )


    # =========================================================
    # 7. CLEAN TEMP FILES
    # =========================================================

    if os.path.exists(input_file):

        os.remove(input_file)


    if os.path.exists(output_file):

        os.remove(output_file)


    # =========================================================
    # 8. FINAL RESULT
    # =========================================================

    print("")
    print("==============================================")
    print("BRONZE → SILVER COMPLETED")
    print("==============================================")

    print(
        f"Rows processed       : {rows_processed:,}"
    )

    print(
        f"Clean rows written   : {rows_written:,}"
    )

    print(
        f"Duplicates removed   : {duplicates_removed:,}"
    )

    print(
        f"Outliers removed     : {outliers_removed:,}"
    )

    print(
        f"Invalid rows removed : {invalid_rows_removed:,}"
    )

    print(
        f"Silver file          : "
        f"s3://{bucket}/{silver_key}"
    )


    return {

        "statusCode": 200,

        "message":
            "Bronze to Silver cleaning completed",

        "source":
            f"s3://{bucket}/{key}",

        "destination":
            f"s3://{bucket}/{silver_key}",

        "rows_processed":
            rows_processed,

        "rows_written":
            rows_written,

        "duplicates_removed":
            duplicates_removed,

        "outliers_removed":
            outliers_removed,

        "invalid_rows_removed":
            invalid_rows_removed
    }
