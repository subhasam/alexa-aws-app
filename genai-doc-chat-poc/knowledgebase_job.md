# Requirement: 
File uploaded by user through an UI Appication to S3, needs to be used to create Knowledgebase on AWS Bedrock, with which the user going to chat with as long the uswer session is active. The created knowledgebase from the user file is confined to that user and categorically,  that conversation of the user. As a AWS Expert, suggest how AWS SDK Boto3 can be used to create the knowledgebase on Bedrock from file on S3 on runtime, pasrt of a user interaction? Bedrock will be using AWS RDS PostgreSQL (with pgvector) as vector database. Generatete a Python program with required Boto3  API than can be run as a Lambda to implement this requirement. Refer the AWS Bedrock, S3 and other required AWS Services documentaion for the implementation

## Step-by-Step Implementation
- *Create a Knowledge Base on AWS Bedrock* : Upload the user file to S3 and create a knowledge base using the Bedrock API.

- *Store Knowledge Base Metadata* : Store the metadata related to the knowledge base in AWS RDS PostgreSQL.

- *Handle User Interaction*: Enable the user to interact with the created knowledge base during their session.

## Overview
Lambda using Pythin and Boto3 that can be executed as an AWS Lambda function to create a knowledge base on AWS Bedrock from a file uploaded to S3. The setup includes S3 for file storage, Bedrock for creating the knowledge base, and AWS RDS PostgreSQL with pgvector for storing vector data.


## Lambda Function Implementation

```python
import json
import os
import boto3
import psycopg2
from botocore.exceptions import ClientError

# Initialize Boto3 clients
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock')
secretsmanager_client = boto3.client('secretsmanager')

# Retrieve PostgreSQL credentials from AWS Secrets Manager
def get_db_credentials():
    secret_name = os.environ['DB_SECRET_NAME']
    response = secretsmanager_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    return secret['username'], secret['password'], secret['host'], secret['dbname']

# Store knowledge base metadata in PostgreSQL
def store_knowledgebase_metadata(conversation_id, knowledgebase_id):
    username, password, host, dbname = get_db_credentials()
    connection = psycopg2.connect(
        dbname=dbname,
        user=username,
        password=password,
        host=host
    )
    cursor = connection.cursor()
    insert_query = """
        INSERT INTO knowledgebase_metadata (conversation_id, knowledgebase_id)
        VALUES (%s, %s)
    """
    cursor.execute(insert_query, (conversation_id, knowledgebase_id))
    connection.commit()
    cursor.close()
    connection.close()

# Create knowledge base on AWS Bedrock
def create_knowledgebase(file_name, bucket_name):
    s3_path = f"s3://{bucket_name}/{file_name}"
    response = bedrock_client.create_knowledgebase(
        DocumentLocation={'S3Object': {'Bucket': bucket_name, 'Name': file_name}},
        DocumentType='pdf'
    )
    return response['KnowledgebaseId']

# Lambda handler function
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        file_name = body['file_name']
        conversation_id = body['conversation_id']
        bucket_name = os.environ['BUCKET_NAME']
        
        knowledgebase_id = create_knowledgebase(file_name, bucket_name)
        store_knowledgebase_metadata(conversation_id, knowledgebase_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'knowledgebase_id': knowledgebase_id})
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }
```
## Key Components:
- Boto3 Clients: Initialize clients for S3, Bedrock, and Secrets Manager.

- PostgreSQL Credentials: Retrieve credentials from AWS Secrets Manager.

- Store Metadata: Use psycopg2 to interact with the PostgreSQL database and store knowledge base metadata.

- Create Knowledge Base: Interact with AWS Bedrock to create a knowledge base from the uploaded file.

## Integration Points:
- S3: For storing and retrieving user-uploaded files.

- AWS Bedrock: For creating the knowledge base.

- AWS RDS PostgreSQL: For storing knowledge base metadata.

- AWS Secrets Manager: For securely managing database credentials.
