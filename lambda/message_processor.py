import json
import os
import logging
import boto3
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize Bedrock Agent Runtime client
# AWS_REGION is automatically set by Lambda runtime
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Environment variables
AGENT_ID = os.environ['BEDROCK_AGENT_ID']
AGENT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process Discord messages by invoking the Bedrock Agent.

    Expected event structure:
    {
        "user_id": "123456789",
        "message": "Hello, what's the weather?"
    }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "response": "The agent's response text"
        }
    }
    """
    try:
        # Extract user message and ID
        user_id = event.get('user_id')
        message = event.get('message')

        if not user_id or not message:
            logger.error(f"Missing required fields. Event: {json.dumps(event)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing user_id or message'})
            }

        logger.info(f"Processing message from user {user_id}: {message[:50]}...")

        # Create session ID from Discord user ID
        session_id = f"discord_user_{user_id}"

        # Invoke Bedrock Agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=message
        )

        # Parse streaming response
        agent_response = parse_agent_response(response)

        logger.info(f"Agent response: {agent_response[:100]}...")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': agent_response,
                'session_id': session_id
            })
        }

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def parse_agent_response(response: Dict[str, Any]) -> str:
    """
    Parse the streaming response from Bedrock Agent.

    The response contains an event stream that we need to iterate through
    to extract the agent's text output.
    """
    agent_response_text = ""

    try:
        # Get the event stream
        event_stream = response['completion']

        # Iterate through events in the stream
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    # Decode the bytes to text
                    chunk_text = chunk['bytes'].decode('utf-8')
                    agent_response_text += chunk_text
            elif 'trace' in event:
                # Log trace information for debugging
                logger.debug(f"Trace event: {json.dumps(event['trace'])}")

        return agent_response_text.strip()

    except Exception as e:
        logger.error(f"Error parsing agent response: {str(e)}", exc_info=True)
        raise
