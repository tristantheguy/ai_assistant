import os
import json
import requests
import re
import subprocess
import argparse
from urllib import parse
from datetime import datetime

FOLDER_PATH = os.path.join(os.path.expanduser("~"), "Documents", "AI Assistant")
ALLOWED_EXT = [".py", ".java", ".cpp", ".js", ".html", ".cs"]
LLM_API_URL = "http://localhost:11434/api/chat"

def read_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        print("❌ File not found.")
        return ""

def sanitize_prompt(prompt):
    # Remove any HTML tags from the prompt
    prompt = re.sub(r"<[^>]*>", "", prompt)
    return prompt

def send_to_llm(prompt, model, timeout=60):
    try:
        response = requests.post(LLM_API_URL, json={
            "model": model,
            "messages": [{"role": "user", "content": sanitize_prompt(prompt)}]
        }, timeout=timeout)

        # Try normal JSON first
        try:
            return response.json()["message"]["content"]
        except json.JSONDecodeError:
            # Fallback for multi-line or streamed responses
            content = ""
            for line in response.text.strip().splitlines():
                try:
                    data = json.loads(line)
                    content += data.get("message", {}).get("content", "")
                except json.JSONDecodeError:
                    continue
            return content or "❌ No response from model."
    except requests.Timeout:
        return f"❌ LLM request timed out."
    except Exception as e:
        return f"❌ LLM communication failed: {e}"

def format_datetime():
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y %H:%M:%S")
    return date_time

def main():
    parser = argparse.ArgumentParser(description='AI Assistant')
    parser.add_argument('--model', default="gpt-3.5-turbo", help='LLM model to use')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout for LLM requests (seconds)')
    args = parser.parse_args()

    print("Welcome to the AI Assistant!")
    model = args.model
    timeout = args.timeout

    while True:
        file_path = input("Enter the path of the file you want me to read (leave empty to exit): ")
        if not file_path:
            break

        if not os.path.isfile(file_path) or not any(file_path.endswith(ext) for ext in ALLOWED_EXT):
            print("Invalid file path.")
            continue

        content = read_file_content(file_path)

        prompt = f"Read and analyze the following code: {content}"

        response = send_to_llm(prompt, model, timeout=timeout)

        print(f"\n{format_datetime()}: LLM Response\n{response}\n")

if __name__ == "__main__":
    main()
