# References 
# https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-setup.html
# https://docs.aws.amazon.com/bedrock/latest/APIReference/welcome.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent/client/create_knowledge_base.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/converse.html#converse
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock.html


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
