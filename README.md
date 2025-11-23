# Alternate History Engine

An AI-powered engine for generating and evolving alternate history timelines. This project uses a multi-model pipeline to propose, debate, and select historical events based on a divergence point.

## Architecture

The system operates on a daily cycle (in-universe time) using a 4-step pipeline:

1.  **Subtopic Generation (Qwen/Grok)**: Selects a specific focus for the day's event based on the universe seed and recent history.
2.  **Model A Proposal (Gemini)**: Proposes a creative, narrative-driven event focused on the subtopic.
3.  **Model B Proposal (DeepSeek)**: Proposes a grounded, realistic event focused on the subtopic.
4.  **Model C Judgment (Groq/Llama)**: Evaluates both proposals and selects the best one (or merges them) to add to the official timeline.

## Tech Stack

-   **Language**: Python
-   **Database**: MongoDB
-   **AI Models**:
    -   Qwen (via OpenRouter)
    -   Gemini (Google)
    -   DeepSeek (via OpenRouter)
    -   Llama 3 (via Groq)

## Setup

1.  **Clone the repository**.
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You may need to create a `requirements.txt` based on the imports in `app.py`)*
3.  **Configure Environment**:
    Create a `.env` file in the root directory with the following keys:
    ```ini
    AI_ML=your_qwen_api_key
    Gemini_Key=your_gemini_api_key
    OpenRouter=your_openrouter_key
    Groq=your_groq_api_key
    MONGO_URI=mongodb://localhost:27017
    ```
4.  **Database**: Ensure MongoDB is running locally or provide a remote URI.

## Usage

Run the main pipeline:

```bash
python app.py
```

The script will:
1.  Connect to MongoDB.
2.  Determine the next day index.
3.  Run the generation pipeline.
4.  Store the results in the `timeline`, `subtopics`, `proposals`, and `judgements` collections.
