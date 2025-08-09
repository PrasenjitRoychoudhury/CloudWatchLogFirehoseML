import json
import boto3
from botocore.exceptions import ClientError

# Initialize clients
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
sns_client = boto3.client('sns', region_name='us-east-1')

# Constants
ENDPOINT_NAME = 'rcf-lambda-duration-endpoint'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:820242904343:Default_CloudWatch_Alarms_Topic'  # <-- Replace with your actual ARN
ANOMALY_THRESHOLD = 1.0

# Sample test data
test_durations = [
    [2.62],
    [2.07],
    [1.92],
    [100.0],
    [0.5],
    [10.0]
]

def lambda_handler(event, context):
    try:
        # Prepare CSV input
        csv_data = '\n'.join([str(x[0]) for x in test_durations])

        # Call SageMaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='text/csv',
            Body=csv_data
        )

        result = json.loads(response['Body'].read().decode('utf-8'))
        scores = [float(item['score']) for item in result.get('scores', result)]

        # Combine durations and scores
        output = [
            {"duration": d[0], "anomaly_score": s}
            for d, s in zip(test_durations, scores)
        ]

        # Check for anomalies
        anomalies = [o for o in output if o["anomaly_score"] > ANOMALY_THRESHOLD]

        # If anomalies found, send alert
        if anomalies:
            message = {
                "alert": "Anomalies detected in Lambda durations.",
                "threshold": ANOMALY_THRESHOLD,
                "anomalies": anomalies
            }
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="⚠️ Lambda Anomaly Alert",
                Message=json.dumps(message, indent=2)
            )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"results": output})
        }

    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"AWS error: {e.response['Error']['Message']}"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Unhandled error: {str(e)}"})
        }
