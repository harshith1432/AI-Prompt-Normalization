# AI Prompt Normalization (Prompt Doctor)

**Prompt Doctor** is an intelligent text processing tool designed to normalize, correct, and enhance user prompts. It utilizes custom data structures and algorithms to handle slang, abbreviations, spelling errors, and grammatical inconsistencies, making it ideal for preprocessing text before it reaches an LLM or search engine.

## 🚀 Features

- **Advanced Normalization**: Expands over 300+ common internet slang terms, abbreviations (e.g., "idk" -> "i don't know", "brb" -> "be right back"), and domain-specific shorthands.
- **Fuzzy Spell Correction**: Implements a **BK-Tree** (Burkhard-Keller Tree) for efficient, distance-based spell checking and correction.
- **Rule-Based Sentence Correction**: A custom engine that reconstructs sentences, fixes capitalization, subject-verb agreement, and handles missing auxiliary verbs without relying on heavy ML models.
- **Intent Detection**: Classifies user inputs into categories like `policy`, `tech`, `howto`, or `chat` based on keyword matching.
- **Inverted Index Retrieval**: Fast keyword-based document retrieval system.
- **Online Learning**: The system learns new vocabulary from user interactions over time (persisted locally).
- **Conversation Memory**: Maintains short-term context of the conversation.

## 🛠️ Tech Stack

- **Python 3.10+**
- **Flask**: Web server and API.
- **Rapidfuzz**: For fast Levenshtein distance calculations.
- **NLTK (Optional)**: Used for POS tagging if available, otherwise falls back to a custom rule-based tagger.

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/harshith1432/AI-Prompt-Normalization.git
   cd AI-Prompt-Normalization
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🏃 Usage

1. **Run the application:**
   ```bash
   python app.py
   ```

2. **Access the Web Interface:**
   Open your browser and navigate to `http://127.0.0.1:5000/`.

3. **API Usage:**
   You can send POST requests to `/api/process`:
   ```json
   POST /api/process
   {
       "text": "idk how to fix the db conn",
       "opts": {
           "spell": true,
           "retrieve": true
       }
   }
   ```

   **Response:**
   ```json
   {
       "reply": "Intent=tech; Found docs=[...]; You said: I do not know how to fix the database connection.",
       "stages": { ... },
       "memory": [ ... ]
   }
   ```

## 📂 Project Structure

- `app.py`: Main Flask application and entry point.
- `ds/`: Core data structures and logic.
  - `bktree.py`: BK-Tree implementation.
  - `inverted_index.py`: Search index implementation.
  - `sentence_corrector.py`: Grammar correction logic.
  - `utils.py`: Normalization and abbreviation data.
  - `memory.py`: Conversation history.
- `data/`: Data storage (dictionaries, documents, learned words).

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.
