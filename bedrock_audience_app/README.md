# Audience-Tailored Content Generator

A web application that uses Amazon Bedrock to generate tailored talking points and questions based on audience profiles.

## Features

- Simple web interface to describe your target audience
- Uses Amazon Bedrock's AI models to generate content tailored to specific audiences
- Provides talking points, discussion questions, and potential objections with responses

## Setup Instructions

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure AWS credentials**

Make sure you have AWS credentials configured with access to Amazon Bedrock. You can set them up using:

```bash
aws configure
```

3. **Run the application**

```bash
python app.py
```

4. **Access the web interface**

Open your browser and go to: http://127.0.0.1:5000

## Usage

1. Enter a detailed description of your audience in the text area
2. Click "Generate Content"
3. Review the tailored talking points, questions, and objection responses

## Requirements

- Python 3.8+
- Flask
- boto3
- AWS account with Amazon Bedrock access
- Appropriate IAM permissions for Bedrock

## Notes

- You may need to request access to specific Bedrock models in your AWS account
- The default model is set to Claude v2, but you can modify the code to use other models
- Adjust the region in app.py to match your preferred AWS region
