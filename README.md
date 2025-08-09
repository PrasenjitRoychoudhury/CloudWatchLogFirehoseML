The github has codes and screenshots for experimentation where AWS Lambda duration duration is subject to observability. If any anomaly is found on the duration there will be notification sent.

1. RCFCodeS3ObjectsRead.py - The training of RCF model based on training data. and sagemaker endpoint deployment.
2. LambdaForSagemakerEndpointInvocation.py - The AWS Lambda code which gets invoked for any new log and invokes sagemaker endpoint for anomaly detection. Send the Amazon SNS notification based on anomaly detection score.
3. NotebookREsourceCleanup.txt - The sagemaker code for clean up of resources related to training and deployment of sagemaker.
4. ApiGatewayforCallingLambda.docx - Screenshots of traffic simulation of Api Gateway invoking AWS Lambda for duration training data set and actual implementation.
5. MainLambdaAsService.docx - AWS Lambda screenshots for microservice which generates logs subject to anomaly detection
6. S3BucketAnomalyDetection.docx - How to test the endpoint of sagemaker
7. SageMakerNotebook.docx - Sagemaker jupyter notebook setup.
8. TransformativeLambdaFireshose.docx - The setup of Transformative Lambda for logs transformation in json format.
