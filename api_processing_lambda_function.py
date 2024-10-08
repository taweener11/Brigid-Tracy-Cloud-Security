# Boilerplate 
import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Set up DynamoDB 
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_table = dynamodb.Table('phi_info')

# Clarify methods 
status_check_path = '/status'
client_path = '/client'
clients_path = '/clients'

# Write lambda function 
def lambda_handler(event, context):
    print('Request event: ', event)
    response = None
   
    try:
        http_method = event.get('httpMethod')
        path = event.get('path')

        # CRUD if-elif-else ladder
        if http_method == 'GET' and path == status_check_path:
            response = build_response(200, 'Brigid and Tracy\'s project is working.')
        elif http_method == 'GET' and path == client_path:
            client_id = event['queryStringParameters']['clientid']
            response = get_client(client_id)
        elif http_method == 'GET' and path == clients_path:
            response = get_clients()
        elif http_method == 'POST' and path == client_path:
            response = save_client(json.loads(event['body']))
        elif http_method == 'PATCH' and path == client_path:
            body = json.loads(event['body'])
            response = modify_client(body['clientid'], body['updateKey'], body['updateValue'])
        elif http_method == 'DELETE' and path == client_path:
            #body = json.loads(event['body'])
            #response = delete_client(body['clientid'])
            client_id = event['queryStringParameters']['clientid']
            response = delete_mod_client(client_id)
        else:
            response = build_response(404, '404 Not Found')

    except Exception as e:
        print('Error:', e)
        response = build_response(400, 'Error processing request')
   
    return response

# Read 
def get_client(client_id):
    try:
        response = dynamodb_table.get_item(Key={'clientid': client_id})
        return build_response(200, response.get('Item'))
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

# Delete, my modified function to use query parameters instead of a JSON object 
def delete_mod_client(client_id):
    try:
        response = dynamodb_table.delete_item(Key={'clientid': client_id})
        return build_response(200, 'Successful deletion.')
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

# Read all 
def get_clients():
    try:
        scan_params = {
            'TableName': dynamodb_table.name
        }
        return build_response(200, scan_dynamo_records(scan_params, []))
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

# Read all helper function 
def scan_dynamo_records(scan_params, item_array):
    response = dynamodb_table.scan(**scan_params)
    item_array.extend(response.get('Items', []))
   
    if 'LastEvaluatedKey' in response:
        scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        return scan_dynamo_records(scan_params, item_array)
    else:
        return {'clients': item_array}

# Create 
def save_client(request_body):
    try:
        dynamodb_table.put_item(Item=request_body)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': request_body
        }
        return build_response(200, body)
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

# Update
def modify_client(client_id, update_key, update_value):
    try:
        response = dynamodb_table.update_item(
            Key={'clientid': client_id},
            UpdateExpression=f'SET {update_key} = :value',
            ExpressionAttributeValues={':value': update_value},
            ReturnValues='UPDATED_NEW'
        )
        body = {
            'Operation': 'UPDATE',
            'Message': 'SUCCESS',
            'UpdatedAttributes': response
        }
        return build_response(200, body)
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

# Delete, note that this function is not called because it uses a JSON object
def delete_client(client_id):
    try:
        response = dynamodb_table.delete_item(
            Key={'clientid': client_id},
            ReturnValues='ALL_OLD'
        )
        body = {
            'Operation': 'DELETE',
            'Message': 'SUCCESS',
            'Item': response
        }
        return build_response(200, body)
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

# Helper 
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Check if it's an int or a float
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        # Let the base class default method raise the TypeError
        return super(DecimalEncoder, self).default(obj)

# Helper 
def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }



