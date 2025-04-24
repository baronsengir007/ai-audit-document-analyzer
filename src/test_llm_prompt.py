import subprocess

def ask_llm(prompt: str):
    result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt,
        capture_output=True,
        text=True  # <- this tells it to treat input/output as strings
    )

    if result.returncode != 0:
        print("Error:", result.stderr)
    else:
        print("Response:\n", result.stdout)

if __name__ == "__main__":
    ask_llm("What is an audit trail and why is it important?")

