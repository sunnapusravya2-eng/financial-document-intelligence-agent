# Financial Document Intelligence Agent for SMEs

An AI-powered financial document intelligence system that automatically processes, classifies, extracts, and analyzes business documents to generate meaningful financial insights.

## 🚀 Overview

Small and medium-sized businesses often manage important financial information across multiple documents such as Profit & Loss statements, Balance Sheets, and Invoices.

The **Financial Document Intelligence Agent** automates this process by combining document processing, financial analysis, and Generative AI to help users understand financial data more efficiently.

Users can upload financial documents and receive structured analysis and AI-powered insights through an interactive Streamlit application.

## ✨ Key Features

* 📄 Upload and process financial documents
* 🔍 Automatic document classification
* 📊 Profit & Loss analysis
* 💰 Balance Sheet analysis
* 🧾 Invoice analysis
* 🤖 Generative AI-powered financial insights
* 📈 Automated financial analysis
* 💬 Interactive Streamlit interface
* 🔐 Environment-based API key configuration

## 🧠 AI & Processing Workflow

```text
Financial Documents
        ↓
Document Upload
        ↓
Document Classification
        ↓
Data Extraction
        ↓
Financial Analysis
        ↓
Generative AI Processing
        ↓
Business Insights
```

## 🛠️ Tech Stack

### Programming

* Python

### Generative AI

* Google Gemini
* Large Language Models (LLMs)
* Generative AI

### AI Application Frameworks

* LangChain
* Streamlit

### Data Processing

* Pandas
* NumPy

### Document Processing

* Excel
* CSV
* PDF

## 📁 Project Structure

```text
financial-document-agent/
│
├── agents/
│   └── document_agent.py
│
├── analysis/
│   └── financial_analysis.py
│
├── extraction/
│   ├── csv_extractor.py
│   ├── excel_extractor.py
│   └── pdf_extractor.py
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/sunnapusravya2-eng/financial-document-intelligence-agent.git
```

### 2. Navigate to the project

```bash
cd financial-document-intelligence-agent
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

#### Windows

```bash
.venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔑 Environment Configuration

Create a `.env` file in the project root:

```text
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

Never commit your real API key to GitHub.

## ▶️ Run the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

The application will open in your browser.

## 📊 Supported Financial Documents

The application is designed to work with financial documents such as:

* Profit & Loss statements
* Balance Sheets
* Invoices
* CSV financial data
* Excel financial data
* PDF financial documents

## 💡 Example Use Case

A business user can upload:

```text
Profit_Loss.xlsx
Balance_Sheet.xlsx
Invoices.xlsx
```

The system can classify the documents, extract relevant financial information, analyze the data, and generate useful financial insights.

## 🎯 Project Goals

The project demonstrates how Generative AI and intelligent document processing can be applied to real-world financial workflows.

The main goal is to reduce manual document analysis and make financial information easier to understand.

## 🔮 Future Enhancements

* Financial forecasting
* Advanced financial risk analysis
* Automated financial reports
* Interactive financial dashboards
* Cloud deployment
* Authentication and authorization
* Multi-user support
* Advanced RAG capabilities
* Agent-based financial recommendations

## 👩‍💻 Author

**Sravya Sunnapu**

Aspiring AI Engineer | Generative AI | RAG | LLMs | Python

GitHub: https://github.com/sunnapusravya2-eng

LinkedIn: https://www.linkedin.com/in/sravyasunnapu/
