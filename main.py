import os
import json
import datetime
import webbrowser
from groq import Groq
from dotenv import load_dotenv

load_dotenv("api_key.env")


INDEX_FILE = "history/index.json"
SESSION_FILE_PREFIX = "session_"
HISTORY_DIR = "history"

MODEL_SPECIALIZATIONS = {
    "llama-3.1-8b-instant": ["shortest", "brief", "concise", "quick", "clear", "simple"],
    "llama-3.1-70b-versatile": ["explanation", "detailed", "in-depth", "comprehensive", "thorough", "elaborate"],
    "image-model-specialized": ["image", "visual", "picture", "graph", "illustration"],
    "gemma2-9b-it": ["detailed", "complex", "extended", "rich", "insightful"],
    "gemma-7b-it": ["in-depth", "thorough", "intensive", "comprehensive", "detailed"],
    "llama-guard-3-8b": ["guarded", "safe", "secure", "protected"],
    "llama3-70b-8192": ["large-context", "extensive", "contextual", "broad"],
    "llama3-8b-8192": ["quick", "medium-context", "responsive", "efficient"],
    "llama3-groq-70b-8192-tool-use-preview": ["tool-use", "preview", "functional", "specialized"],
    "llama3-groq-8b-8192-tool-use-preview": ["tool-use", "preview", "functional", "specialized"],
    "llava-v1.5-7b-4096-preview": ["preview", "specific", "focused", "targeted"],
    "mixtral-8x7b-32768": ["large-context", "expansive", "extended", "wide"]
}


MODEL_COLOR_SHADES = {
    "llama-3.1-8b-instant": [32, 92, 42],  
    "llama-3.1-70b-versatile": [34, 94, 36],
    "gemma2-9b-it": [33, 93, 43],
    "gemma-7b-it": [35, 95, 45], 
    "image-model-specialized": [36, 96, 46],
}

model_response_count = {}

def load_history(session_id):
    filename = get_session_filename(session_id)
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return [{"role": "system", "content": "You are a helpful assistant."}]

def get_index():
    ensure_history_directory()
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r") as file:
            return json.load(file)
    return {"sessions": []}

def update_index(session_id, file_path):
    index = get_index()
    index["sessions"].append({"session_id": session_id, "file_path": file_path})
    with open(INDEX_FILE, "w") as file:
        json.dump(index, file)

def ensure_history_directory():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

def get_session_filename(session_id):
    return os.path.join(HISTORY_DIR, f"{SESSION_FILE_PREFIX}{session_id}.json")

def save_history(session_id, history):
    filename = get_session_filename(session_id)
    with open(filename, "w") as file:
        json.dump(history, file)

def color_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def print_colored_output(result, model):
    shades = MODEL_COLOR_SHADES.get(model, [37])  
    if model not in model_response_count:
        model_response_count[model] = 0
    shade_index = model_response_count[model] % len(shades)
    color_code = shades[shade_index]
    print(color_text(f"\nResponse from {model}:", color_code))
    print(color_text(result, color_code))
    model_response_count[model] += 1

load_dotenv("api_key.env")

def generate_text(messages, model):
    try:
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API Key not found")

        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model
        )
        response_text = chat_completion.choices[0].message.content
        return response_text
    except Exception as e:
        return f"Error: {e}"

def generate_image(prompt):
    try:
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API Key not found")

        client = Groq(api_key=api_key)
        image_response = client.images.generate(prompt=prompt)
        image_url = image_response['data'][0]['url']
        return image_url
    except Exception as e:
        return f"Error generating image: {e}"

def display_image_in_terminal(image_url):
    webbrowser.open(image_url)

def select_model_based_on_keyword(prompt):
    first_word = prompt.lower().split()[0] if prompt.strip() else None
    if first_word:
        for model, keywords in MODEL_SPECIALIZATIONS.items():
            if first_word in keywords:
                if model == "image-model-specialized":
                    return "image"
                return model
    return "llama-3.1-70b-versatile"

def view_history(session_id):
    filename = get_session_filename(session_id)
    if os.path.exists(filename):
        with open(filename, "r") as file:
            history = json.load(file)
            for entry in history:
                role = entry['role']
                content = entry['content']
                print(f"{role.capitalize()}: {content}")
    else:
        print("No history found for this session.")


def interactive_prompt():
    print("Welcome to Terminal GPT with Text and Image Support!")
    session_id = str(datetime.datetime.now().strftime("%Y-%m-%d_%H_%M"))
    first_question_asked = False

    while True:
        user_input = input("Hey boss, how you doing? Friday here (or type 'exit' to quit, 'history' to view history): ")

        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        if user_input.lower() == 'history':
            view_history(session_id)
            continue

        if not first_question_asked:
            first_question_asked = True
            session_filename = get_session_filename(f"{user_input[:50]}_{session_id}")
            update_index(session_id, session_filename)
            history = [{"role": "system", "content": "You are a helpful assistant."}]
        else:
            session_filename = get_session_filename(session_id)
            history = load_history(session_id)

        model = select_model_based_on_keyword(user_input)

        if model == "image":
            image_url = generate_image(user_input)
            if "Error" not in image_url:
                print(f"Image generated: {image_url}")
                display_image_in_terminal(image_url)
            else:
                print(image_url)
        else:
            history.append({"role": "user", "content": user_input})
            result = generate_text(history, model)

            if result:
                if "Error:" in result:
                    print(f"Model {model} failed with error: {result}")
                else:
                    history.append({"role": "assistant", "content": result})
                    print_colored_output(result, model)
            else:
                print("Failed to get a response. Please try again later.")

        save_history(session_id, history)

if __name__ == "__main__":
    interactive_prompt()