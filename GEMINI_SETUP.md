# Gemini API Setup Guide

## Step 1: Get Your Gemini API Key

1. **Visit Google AI Studio**: Go to [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

2. **Sign In**: Sign in with your Google account (Gmail)

3. **Create API Key**:
   - Click on "Create API Key"
   - Choose a name for your API key (e.g., "Legal Analytics Chatbot")
   - Copy the generated API key

## Step 2: Add API Key to Project

1. **Open the secrets file**: `.streamlit/secrets.toml`

2. **Replace the placeholder**:
   ```toml
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```

   Replace `"your_actual_api_key_here"` with your copied API key.

3. **Example**:
   ```toml
   GEMINI_API_KEY = "AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz"
   ```

## Step 3: Restart the Application

After adding the API key, restart your Streamlit application:

```bash
# Stop the current Streamlit app (Ctrl+C)
# Then restart:
streamlit run app.py
```

## Step 4: Test the Chatbot

1. Navigate to the "Legal Chatbot" page in the sidebar
2. Select a case (optional but recommended)
3. Ask questions about legal cases, precedents, or analysis

## Important Notes

- **Security**: Never share your API key publicly
- **Usage Limits**: Gemini API has usage limits. Monitor your usage in Google Cloud Console
- **Cost**: Check Gemini API pricing on the Google Cloud Platform
- **Fallback**: The chatbot will work without the API key but will show a warning message

## Troubleshooting

- **"API key not configured"**: Make sure you've added the key to `.streamlit/secrets.toml`
- **Network errors**: Check your internet connection
- **Rate limits**: If you hit rate limits, wait a few minutes before trying again

## Alternative Setup (Environment Variables)

If you prefer not to use Streamlit secrets, you can set the API key as an environment variable:

```bash
export GEMINI_API_KEY="your_api_key_here"
streamlit run app.py
```

But using `.streamlit/secrets.toml` is recommended for Streamlit applications.