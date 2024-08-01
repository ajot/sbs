from flask import Flask, request, jsonify
import base64
import json
import logging
from config import openai_client, assemblyai_transcriber, airtable_client, airtable_logs_client, RESEND_API_KEY, EMAIL_FROM, EMAIL_TO
import resend
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/inbound', methods=['POST'])
def inbound():
    """Endpoint to receive and process email data."""
    logger.info("Received data via webhook.")
    incoming_data = request.get_json()
    logger.debug(f"Incoming data: {incoming_data}")
    
    return process_incoming_data(incoming_data)

def process_incoming_data(data):
    """Process the incoming data and extract necessary information."""
    logger.debug(f"Processing data: {data}")
    if 'TextBody' in data:
        text_body = data['TextBody']
        logger.info(f"Extracted TextBody: {text_body}")
        extracted_data = extract_info(text_body)
        
        if extracted_data:
            save_to_airtable(extracted_data, text_body)
        else:
            logger.warning("No extracted data to save.")
            log_to_airtable(data, 'No extracted data to save.', text_body)
    else:
        logger.warning("No TextBody found in the email.")
        log_to_airtable(data, 'No TextBody found in the email.')

    attachments = data.get('Attachments', [])
    for attachment in attachments:
        file_name = attachment.get('Name', 'Unnamed')
        file_content = attachment.get('Content')
        content_type = attachment.get('ContentType', 'unknown')

        if not file_content:
            logger.error(f"Missing Content in attachment: {file_name}")
            log_to_airtable(data, f"Missing Content in attachment: {file_name}", text_body)
            continue

        logger.info(f"Processing attachment: {file_name} of type {content_type}")
        
        if content_type.startswith('audio/'):
            process_audio(file_name, file_content)
        elif content_type in ['text/plain']:
            process_document(file_name, file_content, content_type)
        else:
            logger.warning(f"Unsupported content type {content_type} for file {file_name}")

    return jsonify({'status': 'success', 'message': 'Data processed'}), 200

def process_audio(file_name, file_content):
    """Process and transcribe audio attachments."""
    logger.info(f"Processing audio file: {file_name}")
    try:
        # Decode the base64 content and save it as a file
        file_data = base64.b64decode(file_content)
        file_path = f"./downloads/{file_name}"
        with open(file_path, 'wb') as f:
            f.write(file_data)
        logger.info(f"Saved audio file {file_name} at {file_path}")

        # Transcribe the audio file using AssemblyAI
        try:
            logger.info(f"Starting transcription for {file_name}")
            transcript = assemblyai_transcriber.transcribe(file_path)
            transcription_text = transcript.text
            logger.info(f"Transcription completed: {transcription_text}")

            if hasattr(transcript, 'utterances') and transcript.utterances:
                for utterance in transcript.utterances:
                    logger.info(f"Speaker {utterance.speaker}: {utterance.text}")

            # Send the transcription result via email
            send_email("New Transcription from AssemblyAI", transcription_text)

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
    except Exception as e:
        logger.error(f"Error decoding or saving audio file {file_name}: {str(e)}")

def process_document(file_name, file_content, content_type):
    """Process document attachments."""
    logger.info(f"Processing document: {file_name}")
    try:
        # Decode the base64 content and save it as a file
        file_data = base64.b64decode(file_content)
        file_path = f"./downloads/{file_name}"
        with open(file_path, 'wb') as f:
            f.write(file_data)
        logger.info(f"Saved document file {file_name} at {file_path}")

        # Extract text from the document
        text_body = parse_document(file_path, content_type)
        if text_body:
            logger.info(f"Extracted text from document: {text_body}")
            extract_info(text_body)
        else:
            logger.info("No text body found in the document.")

    except Exception as e:
        logger.error(f"Error decoding or saving document {file_name}: {str(e)}")

def parse_document(file_path, content_type):
    """Extract text from the document based on content type."""
    if content_type == 'text/plain':
        with open(file_path, 'r') as file:
            return file.read()
    return None

def extract_info(text):
    """Extract relevant information from text using OpenAI."""
    logger.info("Extracting information using OpenAI")
    logger.info(text)
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
              {"role": "system", "content": "Only return the information asked for. No preamble, and no conclusion. return json."},
              {"role": "user", "content": f"Extract the amount, currency, vendor, and date from the following text. Prioritize the main vendor mentioned in the context of a receipt or transaction, ignoring secondary services or platforms like 'via Paddle.com'. Return the amount as a number, currency as a separate field, and the date in the ISO format (YYYY-MM-DD). {text}. Return in json format."}
            ],
        )
        logger.debug(f"OpenAI response: {response}")

        # Ensure the response structure is as expected
        if response.choices and response.choices[0].message:
            json_content = response.choices[0].message.content
            json_data = json.loads(json_content)
            logger.info(f"Extracted Information: {json_data}")
            return json_data
        else:
            logger.error("Unexpected response structure from OpenAI.")
            return None

    except json.JSONDecodeError as jde:
        logger.error(f"JSON decoding error: {jde}")
        logger.debug(f"Response content: {response.choices[0].message.content if 'choices' in response and response.choices else 'No content'}")
    except Exception as e:
        logger.error(f"Failed to extract information: {e}")

    return None

def save_to_airtable(data, text_body):
    """Save extracted information to Airtable and log the result."""
    logger.info("Saving extracted information to Airtable")
    try:
        record = airtable_client.create(data)
        logger.info(f"Data successfully saved to Airtable: {record['id']}")
        log_to_airtable(data, 'data_saved_successfully', text_body)
    except Exception as e:
        logger.error(f"Error saving data to Airtable: {e}")
        log_to_airtable(data, f"error_saving_data: {str(e)}", text_body)

def log_to_airtable(data, result, text_body=None):
    """Log the result of processing to Airtable logs."""
    log_data = {
        'request_data': json.dumps(data),
        'result': result,
        'text_body': text_body or ''
    }
    try:
        airtable_logs_client.create(log_data)
        logger.info(f"Logged result to Airtable: {result}")
    except Exception as e:
        logger.error(f"Error logging to Airtable: {e}")

def send_email(subject, body):
    """Send an email using Resend API."""
    try:
        logger.info(f"Sending email with subject: {subject}")
        resend.api_key = RESEND_API_KEY
        email_body = f"<strong>{body}</strong>"
        
        response = resend.Emails.send({
            "from": EMAIL_FROM,
            "to": EMAIL_TO,
            "subject": subject,
            "html": email_body
        })
        logger.info(f"Email sent to {EMAIL_TO}. Response: {response}")

    except Exception as e:
        logger.error(f"Failed to send email. Error: {e}")

if __name__ == '__main__':
    # Ensure the downloads directory exists
    os.makedirs("./downloads", exist_ok=True)
    logger.info("Starting Flask app on port 5000.")
    app.run(debug=True)
