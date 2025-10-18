from flask import Flask, request, jsonify, render_template_string
import json
import os
import re
from random import choice

app = Flask(__name__)

# ---------- LOAD KNOWLEDGE BASE ----------
def load_kb(file="knowledge_base.json"):
    """Loads the knowledge base from a JSON file."""
    if not os.path.exists(file):
        print(f"Error: Knowledge base file '{file}' not found!")
        return {}
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{file}'. Make sure it is valid.")
        return {}

# Load the knowledge base once when the app starts
kb = load_kb()

# ---------- MEMORY (Session-based instead of global file) ----------
# In a real web app, you'd use sessions, databases, or another method
# to handle concurrent users. For simplicity, we'll keep the file-based
# memory but acknowledge its limitations.
def load_memory(file="user_memory.json"):
    """Loads user memory from a JSON file."""
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_memory(memory, file="user_memory.json"):
    """Saves user memory to a JSON file."""
    with open(file, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)

# ---------- DYNAMIC INTENT DETECTION LOGIC (from chatbot.py) ----------
def find_best_match(user_input, questions):
    """Finds the best matching question from the knowledge base."""
    user_words = set(re.findall(r'\w+', user_input.lower()))
    if not user_words:
        return None

    best_match = None
    max_score = 0

    for question in questions:
        question_words = set(re.findall(r'\w+', question.lower()))
        score = len(user_words.intersection(question_words))

        if user_input.lower() in question.lower():
            score += 2

        if score > max_score:
            max_score = score
            best_match = question

    return best_match if max_score > 1 else None

def detect_intent(user_input, kb):
    """Detects user's intent dynamically."""
    text = user_input.lower()

    if any(word in text for word in ["bye", "exit", "quit"]):
        return "bye", None

    name_match = re.search(r"(?:my name is|i am|call me)\s+([a-zA-Z]+)", text)
    if name_match:
        return "name", name_match.group(1).capitalize()

    if any(word in text.split() for word in ["hi", "hello", "hey", "heya"]):
        return "greet", None

    best_match_key = find_best_match(text, kb.keys())
    if best_match_key:
        return "question", best_match_key

    return "unknown", None

# ---------- DYNAMIC RESPONSE LOGIC (from chatbot.py) ----------
def get_response(intent, entity, kb, memory):
    """Generates a response based on the detected intent."""
    name = memory.get("name", "")
    
    if intent == "greet":
        greeting = f"Hello {name}!" if name else "Hello!"
        return f"{greeting} I'm your GenAI assistant. You can ask me questions about Generative AI."
    
    elif intent == "name":
        memory["name"] = entity
        save_memory(memory)
        return f"Nice to meet you, {entity}! I'll remember your name."
    
    elif intent == "question":
        return kb.get(entity, "Sorry, I couldn't retrieve the answer.")

    elif intent == "bye":
        farewell = f"Goodbye, {name}!" if name else "Goodbye!"
        return f"{farewell} Keep exploring the world of Generative AI."
        
    elif intent == "unknown":
        return choice([
            "Sorry, I didn't quite get that. Could you rephrase your question?",
            "I'm not sure how to answer that. Try asking about a specific GenAI topic.",
            "Hmm, that's a bit outside my knowledge base. Can you ask me something else?"
        ])

# ---------- API ENDPOINT ----------
@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint."""
    if not kb:
        return jsonify({"response": "Error: Knowledge base not loaded."}), 500
        
    data = request.get_json()
    message = data.get("message", "")
    if not message:
        return jsonify({"response": "Error: No message provided."}), 400

    memory = load_memory()
    intent, entity = detect_intent(message, kb)
    response = get_response(intent, entity, kb, memory)
    
    return jsonify({"response": response})

@app.route("/")
def home():
    """A simple status page to show the API is running."""
    return "<h1>GenAI Chatbot Flask API</h1><p>The API is running. Use the /chat endpoint to interact.</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
