# Chatbot with Document Interaction

## Installation Instructions

1. **Install Required Packages**

   Run the following command to install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**

   Ensure your OpenAI API key is included in the `.env` file.

## Using LLaMA3 Model from Ollama

### Installation of Ollama

#### For Linux:

   Run this command:

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

#### For Windows:

   Download Ollama from the [official website](https://ollama.com/download/windows).

### Pull the LLaMA3 Model

After installing Ollama, you need to pull the LLaMA3 model. Run the following commands:

   ```bash
   ollama serve
   ollama pull llama3
   ```

## Configuration

You can modify any parameters in the `config.chain_config` file to suit your needs.

## Running the Streamlit Application

To run the Flask Web application, use the following command:

   ```bash
   python app.py
   ```