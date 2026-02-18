# 📚 API and Architectural Documentation

This document provides a deep dive into the internal workings of the AI Prompt Normalization (Prompt Doctor) system.

## 1. System Architecture

The application is built as a pipeline where text flows through several stages of transformation:

1.  **Input**: Raw user text (e.g., "u gonna fix teh db?").
2.  **Normalization**: Expands abbreviations and slang (e.g., "you are going to fix the database").
3.  **Tokenization & Spell Correction**: Splits text and corrects typos using a BK-Tree.
4.  **Sentence Correction**: Reconstructs the sentence grammar (e.g., "Are you going to fix the database?").
5.  **Intent & Retrieval**: Analyzes intent and searches relevant documents.
6.  **Response**: Returns the processed text and any findings.

## 2. Core Modules (`ds/`)

### 2.1 Normalization (`ds/utils.py`)
This module handles the initial cleaning of the text.
-   **Method**: `normalize(text)`
-   **Logic**:
    -   Converts to lowercase.
    -   Replaces over 300 defined abbreviations using regex word boundaries (e.g., `\bbrb\b` -> `be right back`).
    -   Removes special characters and extra whitespace.
    -   **Abbreviation List**: Includes categories like internet slang ("lol", "idk"), technical terms ("db", "repo", "ux"), and polite phrases ("ty", "pls").

### 2.2 BK-Tree Spell Correction (`ds/bktree.py`)
Used for efficient fuzzy matching of words against a dictionary.
-   **Algorithm**: [Burkhard-Keller Tree](https://en.wikipedia.org/wiki/BK-tree).
-   **Functionality**:
    -   `add(word)`: Inserts a word into the tree.
    -   `query(word, max_dist=1)`: Finds all words in the dictionary within a Levenshtein edit distance of `max_dist`.
-   **Performance**: Much faster than checking every word in the dictionary, as it prunes large branches of the search space based on triangle inequality.
-   **Deduping**: Also attempts to handle letter elongation (e.g., "pleeeease" -> "please") before checking.

### 2.3 Sentence Correction (`ds/sentence_corrector.py`)
A rule-based engine to make the text grammatically correct.
-   **Tagging**: Attempts to use `nltk.pos_tag` if available; otherwise, falls back to a custom heuristic tagger based on suffixes (`-ing`, `-ed`, `-ly`) and common word lists.
-   **Logic**:
    -   **Subject Identification**: Finds pronouns or nouns to act as the subject. Defaults to "I" or "It" if missing.
    -   **Verb Phrase Construction**: Identifies verbs, handles future markers ("gonna" -> "will"), and negation ("not").
    -   **Object/Adjective Ordering**: Ensures adjectives precede nouns.
    -   **Question Formulation**: Detects WH-words (what, why, how) and restructures the sentence (e.g., "how install" -> "How do I install?").
    -   **Formatting**: Capitalizes the first letter and ensures proper punctuation.

### 2.4 Inverted Index (`ds/inverted_index.py`)
Provides keyword-based document search.
-   **Structure**: A dictionary mapping words (terms) to a set of document IDs.
-   **Searching**: `search_all(query)` tokenizes the query and returns the intersection of documents containing those terms.

### 2.5 Conversation Memory (`ds/memory.py`)
-   **Structure**: Uses a `deque` with a fixed maximum length (default 8) to store recent user and assistant messages.
-   **LRU Cache**: A simple implementation of a Least Recently Used cache is also included (though primarily for demonstration).

## 3. Data Management

-   **`data/dictionary.txt`**: The base vocabulary for spell checking.
-   **`data/docs/`**: Text files placed here are automatically indexed on startup.
-   **`data/user_learned.txt`**: Words that the system has "learned" from the user (seen > 2 times) are persisted here to survive restarts.

## 4. API Reference

### `POST /api/process`

Processes the input text and returns the normalized/corrected version.

**Request Header**: `Content-Type: application/json`

**Request Body**:
| Field | Type | Description |
| :--- | :--- | :--- |
| `text` | string | The raw user input string. |
| `opts` | object | Optional settings. |
| `opts.spell` | boolean | Enable/disable spell correction (default: `true`). |
| `opts.retrieve` | boolean | Enable/disable document retrieval (default: `true`). |

**Response Body**:
```json
{
  "reply": "Constructed response string...",
  "stages": {
    "normalize": { "normalized": "...", "ms": 0.1 },
    "tokenize_spell": { "corrected_text": "...", "ms": 2.5 },
    "sentence": { "corrected": "...", "ms": 1.2 },
    "intent": { "intent": "tech", "ms": 0.05 },
    "retrieval": { "docs": [], "ms": 0.1 }
  },
  "memory": [
    { "role": "user", "text": "..." },
    { "role": "assistant", "text": "..." }
  ],
  "learned": []
}
```
