import os
from dotenv import load_dotenv
import assemblyai as aai
from openai import OpenAI
from pyairtable import Table

# Load environment variables from .env file
load_dotenv()

# Set API keys and Airtable details
ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
EMAIL_FROM = os.getenv('RESEND_EMAIL_FROM')
EMAIL_TO = os.getenv('RESEND_EMAIL_TO')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_RECEIPT_PROCESSOR_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_RECEIPT_PROCESSOR_BASE_ID')
AIRTABLE_TABLE_NAME_RECEIPTS = "receipts-inbox"
AIRTABLE_TABLE_NAME_LOGS = "logs"

# OpenAI and AssemblyAI client initialization
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
aai.settings.api_key = ASSEMBLYAI_API_KEY
assemblyai_transcriber = aai.Transcriber()

# Initialize Airtable client
airtable_client = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_RECEIPTS)
airtable_logs_client=Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_LOGS)
