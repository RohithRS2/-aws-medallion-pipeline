# AWS Medallion Data Pipeline

## Overview

This project demonstrates an AWS-based Medallion Architecture for processing transaction data through three layers:

**Bronze → Silver → Gold**

The pipeline uses Amazon S3 and AWS Lambda to automatically process and transform data as it moves between the layers.

## Architecture

```text
Raw CSV
   |
   v
S3 Bronze Layer
   |
   | S3 Event Trigger
   v
AWS Lambda
Bronze → Silver
   |
   v
S3 Silver Layer
   |
   | S3 Event Trigger
   v
AWS Lambda
Silver → Gold
   |
   v
S3 Gold Layer


Bronze Layer

The Bronze layer stores raw transaction data uploaded to Amazon S3.

Example:

bronze/

Silver Layer

The Bronze-to-Silver Lambda processes the raw data and creates a cleaned dataset.

Processing includes:

* Data cleaning
* Duplicate removal
* Invalid/outlier record removal
* Transaction data transformation
* Creation of a clean CSV dataset

Output:

silver/clean_transactions.csv

Gold Layer

The Silver-to-Gold Lambda creates an analytics-ready aggregated dataset.

Processing includes:

* Grouping transactions by product category
* Calculating transaction counts
* Calculating total transaction amounts
* Creating the final Gold dataset

Output:

gold/gold_transactions.csv

AWS Services Used

* Amazon S3
* AWS Lambda
* AWS IAM
* Amazon SNS
* Amazon CloudWatch

Lambda Functions

Bronze to Silver

File:

lambda/bronze-to-silver/lambda_function.py

Triggered when a CSV file is uploaded to the Bronze S3 layer.

Responsibilities:

* Read the Bronze CSV file
* Clean transaction data
* Remove duplicate records
* Remove invalid/outlier records
* Write the cleaned data to Silver

Silver to Gold

File:

lambda/silver-to-gold/lambda_function.py

Triggered when a CSV file is created in the Silver S3 layer.

Responsibilities:

* Read the Silver dataset
* Aggregate transactions by category
* Calculate transaction counts
* Calculate total transaction amounts
* Write the Gold dataset to S3

Event-Driven Architecture

The pipeline automatically processes files using S3 object-created events.

CSV Upload
    |
    v
S3 Bronze
    |
    v
Bronze-to-Silver Lambda
    |
    v
S3 Silver
    |
    v
Silver-to-Gold Lambda
    |
    v
S3 Gold


IAM

IAM roles provide Lambda with the required permissions to read and write objects in Amazon S3.

AWS credentials are not stored in this repository.

Monitoring and Notifications

AWS CloudWatch can be used to monitor Lambda execution, logs, duration, memory usage, and failures.

Amazon SNS is used for notification capabilities.

Project Structure

aws-medallion-pipeline/
│
├── lambda/
│   ├── bronze-to-silver/
│   │   └── lambda_function.py
│   │
│   └── silver-to-gold/
│       └── lambda_function.py
│
└── README.md

Technologies

* Python
* Amazon S3
* AWS Lambda
* AWS IAM
* Amazon SNS
* Amazon CloudWatch
* CSV Processing
* Event-Driven Architecture
* Medallion Architecture
* ETL

Key Learning Outcomes

This project demonstrates practical experience with:

* AWS S3 data lake architecture
* Medallion Architecture
* Serverless data processing
* Event-driven processing
* Python-based ETL
* Data cleaning and transformation
* Data aggregation
* IAM permissions
* AWS monitoring and notifications
