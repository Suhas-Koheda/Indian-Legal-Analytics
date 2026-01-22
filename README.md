# Legal Analytics Dashboard

A comprehensive dashboard for analyzing Supreme Court legal cases with advanced analytics and AI-powered insights.

## Features

- **Overview**: Dashboard summary with key metrics and trends
- **Judge Analytics**: Individual judge performance and career analysis
- **Case Explorer**: Search and browse individual cases with detailed information
- **Citation Analytics**: Citation frequency and trend analysis
- **Petitioner/Respondent**: Party analysis and litigation patterns
- **Legal AI Assistant**: Advanced LangChain-powered legal analysis with Gemini AI

## Setup

### 1. Install Dependencies

**Basic installation (core features only):**
```bash
pip install streamlit pandas matplotlib beautifulsoup4 lxml requests tqdm
```

**Full installation (with AI chatbot):**
```bash
pip install -r requirements.txt
# OR manually:
pip install streamlit pandas matplotlib beautifulsoup4 lxml requests tqdm langchain-google-genai langchain-core
```

### 2. Set up Gemini API Key (Optional)

The AI chatbot requires a Google Gemini API key for advanced legal analysis:

1. **Get your free API key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Enter it securely** in the chatbot sidebar when prompted
3. **Storage**: API key is stored locally in your browser session only
4. **Privacy**: Key never leaves your browser or gets logged

**🔒 Security Implementation**: [View how your API key is securely handled](https://github.com/Suhas-Koheda/Indian-Legal-Analytics/blob/main/pages/7_Chatbot.py#L123)

**Without API key**: Basic case search still works, AI features disabled.

### 3. Run the Preprocessing Script
```bash
python preprocessing.py
```

### 4. Start the Dashboard
```bash
streamlit run app.py
```

## Data Processing

The preprocessing pipeline:
1. Combines yearly parquet files from `parquet_metadata/`
2. Normalizes judge, citation, and party information
3. Extracts petitioner/respondent from case titles
4. Generates analytics datasets for judges and citations

## Usage

- Use the sidebar to navigate between different analysis pages
- Filter data by year ranges and search terms
- The chatbot can provide legal analysis and answer questions about cases
- All visualizations are interactive and exportable

## Data Sources

- Supreme Court judgment metadata (1950-2025)
- Case text and structured legal information
- Judge and citation analytics

## Dependencies

### Core Packages
- **streamlit**: Web application framework for the dashboard
- **pandas**: Data manipulation and analysis
- **matplotlib**: Plotting and data visualization
- **beautifulsoup4 + lxml**: HTML parsing for data extraction
- **requests**: HTTP requests for API calls

### AI & LangChain
- **langchain-google-genai**: Google Gemini integration
- **langchain-core**: Core LangChain functionality
- **tqdm**: Progress bars for data processing

### Optional Packages
- **seaborn**: Enhanced statistical plotting
- **plotly**: Interactive visualizations
- **openpyxl/xlrd**: Excel file support
- **pytest**: Testing framework
- **black**: Code formatting

## Contributing

Ensure all code follows the established patterns:
- No comments in production code
- Minimal emojis (only functional UI elements)
- Proper error handling and caching
- Consistent data processing patterns