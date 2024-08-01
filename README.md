### Simple Butler Service

A backend service designed to handle specific everyday tasks through email/sms. https://github.com/ajot/simple_butler_service. It currently does two things:

1. **Invoice and Receipt Processing**:
   - Forward your invoices or receipts via email (using [Postmark](https://postmarkapp.com)
   - The service extracts key details like amount, vendor, and date.
   - These details are logged into [Airtable](https://airtable.com) for easy access.

2. **Audio Note Transcription**:
   - Send audio notes via email
   - The service transcribes them using [AssemblyAI](assemblyai.com) and emails the text back to you using [Resend](https://resend.com).

Learn more about it on [curiousmints.com](https://www.curiousmints.com/simple-butler-service-to-automate-everyday-tasks/)

## Getting Started

### Prerequisites

- Python 3.x
- AssemblyAI API key
- Resend API key
- Airtable API key
- Postmark account

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ajot/simple_butler_service.git
   cd simple_butler_service
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**

   Create a `.env` file in the project root:

   ```env
   ASSEMBLYAI_API_KEY=your_assemblyai_api_key
   RESEND_API_KEY=your_resend_api_key
   RESEND_EMAIL_FROM=your_email@example.com
   RESEND_EMAIL_TO=recipient_email@example.com
   AIRTABLE_API_KEY=your_airtable_api_key
   AIRTABLE_BASE_ID=your_airtable_base_id
   AIRTABLE_TABLE_NAME=your_airtable_table_name
   ```

4. **Create Downloads Directory**

   ```bash
   mkdir -p downloads
   ```

## How It Works

### Invoice and Receipt Processing

1. **Forward your invoice or receipt email to the service.**
2. **Key details are extracted and logged into Airtable.**

### Audio Note Transcription

1. **Send an email with an audio attachment.**
2. **The audio is transcribed and the text is emailed back.**

## Running the App

Start the Flask app:

```bash
python app.py
```

For testing with Postmark, use ngrok:

```bash
ngrok http 4000
```

Update Postmark's webhook with your ngrok URL and `/inbound`.