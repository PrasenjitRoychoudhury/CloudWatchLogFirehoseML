import json
import boto3
import sagemaker
from sagemaker import RandomCutForest
import pandas as pd
import numpy as np
import io
import requests

# Initialize AWS clients
sagemaker_session = sagemaker.Session()
s3_client = boto3.client('s3')
role = 'role/datazone_usr_role_apqb1fy6suzx2f_dbwax57m3g5xyf'  # Replace with your SageMaker role ARN
bucket = 'prc-s3bucket-firehose-ml-poc-1xfsfx121312xxrere2'  # Replace with your S3 bucket name
prefix = 'sagemaker/rcf-lambda-duration'

# Function to extract durations from log
def extract_durations(log_data):
    durations = []
    for entry in log_data:
        if entry['eventType'] == 'REPORT' and 'durationMs' in entry:
            durations.append(float(entry['durationMs']))
    return durations

# List and process all objects in the S3 prefix
s3_prefix = '2025/07/19/09/'
durations = []
try:
    # List objects in the S3 bucket under the specified prefix
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=s3_prefix)
    if 'Contents' not in response or not response['Contents']:
        raise Exception(f"No objects found in s3://{bucket}/{s3_prefix}")

    for obj in response['Contents']:
        key = obj['Key']
        # Generate a presigned URL for each object
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=1800
        )
        # Fetch and process the log data from the presigned URL
        response = requests.get(presigned_url)
        if response.status_code == 200:
            log_data = [json.loads(line) for line in response.text.splitlines() if line.strip()]
            durations.extend(extract_durations(log_data))
        else:
            print(f"Failed to fetch log file {key}: {response.status_code} - {response.text}")

    if not durations:
        raise Exception("No valid durations extracted from any log files")
except Exception as e:
    raise Exception(f"Error processing S3 objects: {str(e)}")

# Convert to DataFrame and save to CSV
df = pd.DataFrame(durations, columns=['duration_ms'])
csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False, header=False)

print(prefix)

# Upload data to S3
s3_key = f'{prefix}/input/durations.csv'
s3_client.put_object(Bucket=bucket, Key=s3_key, Body=csv_buffer.getvalue())


# Define S3 paths
train_input = f's3://{bucket}/{s3_key}'


# Configure RCF estimator
rcf = RandomCutForest(
    role=role,
    instance_count=1,
    instance_type='ml.m5.large',
    data_location=train_input,
    output_path=f's3://{bucket}/{prefix}/output',
    num_samples_per_tree=512,
    num_trees=50,
    sagemaker_session=sagemaker_session
)


# Train the model
try:
    rcf.fit(rcf.record_set(df.values.astype('float32')))
    print(f"Model training completed. Output saved to s3://{bucket}/{prefix}/output")
except ClientError as e:
    error_code = e.response['Error']['Code']
    error_message = e.response['Error']['Message']
    raise Exception(f"SageMaker training failed: {error_code} - {error_message}")

# Optional: Deploy the model for inference
# predictor = rcf.deploy(initial_instance_count=1, instance_type='ml.m5.large')


# Deploy the model to an endpoint
try:
    endpoint_name = 'rcf-lambda-duration-endpoint'
    predictor = rcf.deploy(
        initial_instance_count=1,
        instance_type='ml.m5.large',
        endpoint_name=endpoint_name
    )
    print(f"Model deployed to endpoint: {endpoint_name}")
except ClientError as e:
    error_code = e.response['Error']['Code']
    error_message = e.response['Error']['Message']
    raise Exception(f"Endpoint deployment failed: {error_code} - {error_message}")
	
