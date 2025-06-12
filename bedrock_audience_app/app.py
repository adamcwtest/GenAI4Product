import os
from flask import Flask, render_template, request, jsonify
import boto3
import json

app = Flask(__name__)

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'  # Change to your preferred region
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    # Get audience profile from request
    audience_profile = request.form.get('audience_profile')
    
    if not audience_profile:
        return jsonify({'error': 'Audience profile is required'}), 400
    
    # Prepare prompt for Bedrock
    prompt = f"""
    Based on the following audience profile, generate a set of tailored talking points 
    and engaging questions that would resonate well with this specific audience.
    
    Audience Profile: {audience_profile}
    
    Please provide:
    1. 5 key talking points that would resonate with this audience
    2. 3 engaging questions to spark discussion with this audience
    3. 2 potential objections this audience might have and how to address them
    """
    
    try:
        # Call Bedrock with Claude model
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-v2',  # You can change to your preferred model
            body=json.dumps({
                "prompt": f"Human: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 2000,
                "temperature": 0.7,
                "top_p": 0.9,
            })
        )
        
        # Parse response
        response_body = json.loads(response.get('body').read())
        generated_content = response_body.get('completion', '')
        
        return jsonify({
            'talking_points': generated_content
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
