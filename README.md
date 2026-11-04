# FinAssist AI

An AI-powered banking customer-support prototype demonstrating **Generative AI, Retrieval-Augmented Generation (RAG), and AI Agent tool calling**.

FinAssist AI uses a Large Language Model (LLM) to answer banking-related questions using retrieved policy information and interact with a synthetic transaction database through dedicated tools.

## Features

- **RAG-based policy retrieval:** Uses Sentence Transformers and FAISS to retrieve relevant information from a knowledge base containing selected summaries of publicly available DBS Singapore webpages.
- **AI Agent tool calling:** Allows the LLM to decide when to retrieve policy information or look up transaction records.
- **Synthetic transaction lookup:** Queries a SQLite database containing demonstration customer and transaction records.
- **Customer-scoped queries:** Restricts transaction lookups to the demo customer currently selected in the interface.
- **Safety and grounding instructions:** Guides the chatbot to avoid unsupported banking claims, protect sensitive information and communicate its limitations.
- **Evaluation framework:** Includes retrieval and answer evaluation to assess retrieval performance and the factual grounding of generated responses.
- **Gradio interface:** Provides an interactive chatbot interface for testing the prototype.

## Requirements

- Python 3.12
- Groq API key

## Setup and Installation

### 1. Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install groq gradio python-dotenv sentence-transformers faiss-cpu pytest
```

### 3. Configure the API key

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_actual_groq_api_key
```

Do not share this file or commit it to GitHub.

### 4. Run the application

```bash
python app.py
```

Open the local Gradio URL displayed in the terminal.

## Project Structure

```text
finassist-ai/
│
├── app.py                  # Main chatbot, LLM integration, agent
│                           # tool calling, safety instructions and UI
│
├── rag.py                  # Document processing, embeddings,
│                           # FAISS indexing and policy retrieval
│
├── database.py             # SQLite database and transaction
│                           # lookup functions
│
├── evaluate_rag.py         # Retrieval evaluation
│
├── evaluate_answers.py     # End-to-end answer evaluation
│
├── data/
│   ├── banking_faqs.md     # Demonstration banking FAQs (removed)
│   ├── banking_policies.md # Demonstration banking policies (removed)
│   ├── 02_dbs_fraud_reporting.md
│   ├── 03_dbs_transaction_disputes.md
│   ├── 04_dbs_lost_stolen_cards.md
│   ├── 05_dbs_fees_and_charges.md
│   └── transactions.db     # Synthetic transaction records
│
├── evaluations/             # Evaluation datasets and results
│
├── .env                     # API credentials (not committed)
└── README.md
```

*The project structure may vary slightly depending on generated files and local configuration.*

## Evaluation

FinAssist AI includes two evaluation components:

**1. Retrieval Evaluation (`evaluate_rag.py`)**

Evaluates whether the RAG system retrieves relevant knowledge-base passages for a set of test questions.

**2. Answer Evaluation (`evaluate_answers.py`)**

Evaluates the chatbot's end-to-end responses, including:
- Whether the appropriate tool was called.
- Whether relevant policy passages were retrieved.
- Whether generated answers remain grounded in the retrieved information.
- Whether unsupported claims or inaccuracies appear in the responses.

Run the evaluation scripts:

```bash
python evaluate_rag.py
python evaluate_answers.py
```

Evaluation results are saved separately to support comparison between different versions of the system.

## Technologies Used

| Component | Technology |
|---|---|
| Programming language | Python 3.12 |
| LLM provider | Groq API |
| Language model | OpenAI GPT-OSS 20B (via Groq) |
| RAG framework | Custom implementation |
| Embedding model | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector database | FAISS |
| Transaction database | SQLite |
| User interface | Gradio |

## Limitations and Disclaimer

FinAssist AI is an independent academic prototype and is **not affiliated with, endorsed by, or an official service of DBS Bank**.

- DBS-related information is based on selected summaries of publicly available information and may not cover all products, services or policies.
- Policy information may change. Users should refer to official DBS channels for current information.
- Transaction records and customer profiles are synthetic and used exclusively for demonstration.
- The prototype does not connect to actual bank accounts or access real customer information.
- It cannot execute banking transactions, freeze cards, activate security features, submit disputes or contact the bank.
- Generated responses may contain inaccuracies and should not be relied upon as financial or banking advice.

**Always verify important banking information through official DBS channels.**