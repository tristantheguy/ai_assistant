import argparse
import subprocess
import os

GUI_SCRIPT = "gui_interface.py"
CLI_SCRIPT = "code_assistant.py"

MODEL_OPTIONS = {
    "openhermes:latest": "4.1 GB",
    "dolphin-mixtral:8x7b": "26 GB",
    "mistral:latest": "4.1 GB"
}

def choose_model():
    print("📦 Available Models:")
    for i, (model, size) in enumerate(MODEL_OPTIONS.items(), 1):
        print(f"{i}. {model} ({size})")
    while True:
        choice = input("👉 Select a model by number: ")
        if choice.isdigit() and 1 <= int(choice) <= len(MODEL_OPTIONS):
            return list(MODEL_OPTIONS.keys())[int(choice)-1]
        else:
            print("❌ Invalid selection. Please enter a valid number.")

def run_script(script_path, model):
    try:
        subprocess.run(["python", script_path, "--model", model], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run {script_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="AI Code Assistant Launcher")
    parser.add_argument("--gui", action="store_true", help="Launch the GUI interface")
    parser.add_argument("--cli", action="store_true", help="Launch the command-line interface")
    args = parser.parse_args()

    model = choose_model()

    if args.gui:
        run_script(GUI_SCRIPT, model)
    elif args.cli:
        run_script(CLI_SCRIPT, model)
    else:
        print("⚠️  Please specify --gui or --cli to run the desired interface.")

if __name__ == "__main__":
    main()
