# AWS Cloud Infrastructure

This directory contains the AWS cloud components used by the electronic toll
collection prototype developed for the PSI5120 final project.

## Architecture

The cloud processing workflow uses the following AWS services:

- **Amazon S3** – stores images captured by the Raspberry Pi.
- **AWS Lambda** – coordinates the cloud processing workflow.
- **Amazon Rekognition** – performs text detection on the captured images.
- **Amazon DynamoDB** – stores the vehicle license plate authorization records.
- **AWS IoT Core** – publishes the authorization result back to the Raspberry Pi.
- **AWS IAM** – defines the permissions required by the Lambda function and IoT
  components.

The processing sequence is:

1. The Raspberry Pi captures an image and uploads it to Amazon S3.
2. Creation of a `.jpg` object in the S3 bucket triggers the Lambda function.
3. The Lambda function calls Amazon Rekognition to detect text in the image.
4. The detected text is processed to identify a valid Brazilian license plate.
5. If a valid plate is detected, DynamoDB is queried for its authorization status.
6. The Lambda function publishes the result through AWS IoT Core using MQTT.
7. The Raspberry Pi receives the result and activates the corresponding local
   actuator.

## Directory Structure

```text
aws/
├── cloudformation/
│   └── psi5120-toll-iot.yaml
├── lambda/
│   └── lambda_function.py
└── README.md

cloudformation/
Contains the CloudFormation template generated from the deployed AWS
infrastructure using the AWS CloudFormation IaC Generator.

The template documents the main resources used by the prototype, including:

S3 bucket

Lambda function

DynamoDB table

AWS IoT Thing

AWS IoT Policy

IAM role and policies

S3-to-Lambda event notification

Lambda invocation permission

The generated template represents a snapshot of the deployed infrastructure.
Some deployment-specific properties, particularly the Lambda deployment package,
are represented as CloudFormation parameters. Therefore, the template should be
considered infrastructure documentation and a basis for reproducing the
environment rather than a completely self-contained deployment package.

lambda/
Contains the Python source code executed by the AWS Lambda function.

The Lambda function is responsible for:

receiving S3 object creation events;

requesting text detection from Amazon Rekognition;

extracting and validating candidate license plates;

querying the DynamoDB authorization table;

publishing the authorization result to AWS IoT Core; and

collecting processing-time measurements used in the experimental evaluation.

Main AWS Resources
Resource	   Name
S3 Bucket	    psi5120-toll-captures
Lambda Function	psi5120-toll-image-processor
DynamoDB Table	plateList
IoT Thing	    psi5120-toll-raspberry
IoT Policy	    psi5120-toll-raspberry-Policy
MQTT Result Topic	toll/result/psi5120-toll-raspberry
AWS Region	us-east-1
￼
The DynamoDB table uses plate as its primary key. The S3 bucket is configured
to invoke the Lambda function when a .jpg object is created.

Security
Credentials, AWS access keys, IoT private keys, and certificates are intentionally
not included in this repository.

The CloudFormation template contains resource identifiers and IAM configuration
used by the experimental environment, but no authentication credentials.

Notes
The infrastructure was originally created and configured in AWS and subsequently
exported using the AWS CloudFormation IaC Generator. The included CloudFormation
template therefore reflects the configuration of the experimental environment
used to obtain the results reported in the accompanying paper.
