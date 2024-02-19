import glob
import os
import readline
import signal
import subprocess

from jinja2 import Environment, FileSystemLoader
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
template_dir = "."

last_output = ""
last_command = ""
current_directory = ""
env = Environment(loader=FileSystemLoader(template_dir))
system_tpl = env.get_template("system.j2")
user_tpl = env.get_template("user.j2")


always_run = False


def start_persistent_shell():
    global persistent_shell
    if "persistent_shell" in globals():
        try:
            persistent_shell.stdin.close()
            persistent_shell.terminate()
            persistent_shell.wait()
        except Exception as e:
            print(f"Error closing previous shell: {e}")
    persistent_shell = subprocess.Popen(
        [get_shell()],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )


def get_concise_git_status():
    try:
        # Send git status command to the persistent shell
        persistent_shell.stdin.write("git status --porcelain 2> /dev/null\n")
        persistent_shell.stdin.flush()
        persistent_shell.stdin.write("echo '__END_OF_GIT_STATUS__'\n")
        persistent_shell.stdin.flush()

        status_lines = []
        while True:
            line = persistent_shell.stdout.readline()
            if "__END_OF_GIT_STATUS__" in line:
                break
            if line.strip():  # Ignore empty lines
                status_lines.append(line.strip())

        if not status_lines:
            return "○ "  # No changes

        # Check for unstaged and staged changes
        staged = any(
            line.startswith("A ") or line.startswith("M ") or line.startswith("D ")
            for line in status_lines
        )
        unstaged = any(
            line.startswith(" M") or line.startswith(" D") or line.startswith("??")
            for line in status_lines
        )

        if staged and unstaged:
            return "🟢🔴 "  # Both staged and unstaged changes
        elif staged:
            return "🟢 "  # Only staged changes
        elif unstaged:
            return "🔴 "  # Only unstaged changes
    except Exception as e:
        while True:
            # Try to read a line, non-blocking
            try:
                line = persistent_shell.stdout.readline()
                if "__END_OF_GIT_STATUS__" in line:
                    break
            except Exception as e:
                break

        return "○ "  # Not a git repository or other error


def signal_handler(sig, frame):
    print("\nOperation cancelled by user. Restarting shell...")
    start_persistent_shell()  # Restart the shell to cancel the current running command
    main_loop()  # Return to the main input loop


signal.signal(signal.SIGINT, signal_handler)


def get_dwim(input):
    global last_command, last_output
    system_cnt = system_tpl.render(
        {
            "shell": get_shell(),
        }
    )
    user_cnt = user_tpl.render(
        {"last_command": last_command, "last_output": last_output, "input": input}
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_cnt,
            },
            {
                "role": "user",
                "content": user_cnt,
            },
        ],
        model="gpt-3.5-turbo",
    )
    return chat_completion.choices[0].message.content


def complete(text, state):
    base_path = glob.glob(current_directory + "/" + text + "*")
    options = [x[len(current_directory) + 1 :] for x in base_path]
    try:
        return options[state]
    except IndexError:
        return None


def prefill_hook(text):
    readline.insert_text(text)
    readline.redisplay()


def get_shell():
    return os.environ.get("SHELL", "/bin/bash")


def run_command(command):
    global last_command, last_output
    last_command = command
    last_output = ""
    print(f"meaning> {command}")

    # Send command to the persistent shell
    persistent_shell.stdin.write(command + "\n")
    persistent_shell.stdin.flush()

    # Mark the end of command output
    persistent_shell.stdin.write("echo '__END_OF_COMMAND__'\n")
    persistent_shell.stdin.flush()
    persistent_shell.stdin.write("echo '__END_OF_STDERR__' >&2\n")
    persistent_shell.stdin.flush()

    # Read from stdout
    while True:
        line = persistent_shell.stdout.readline()
        if "__END_OF_COMMAND__" in line:
            break
        last_output += line
        print(line, end="")

    # Now, read from stderr to capture any errors
    error_output = ""
    while True:
        line = persistent_shell.stderr.readline()
        if "__END_OF_STDERR__" in line:
            break
        error_output += line
        print(line, end="")  # Print errors to the console

    if error_output:
        print("Error detected in command execution:")
        print(error_output)


def get_current_directory():
    global current_directory
    # Send 'pwd' command to the persistent shell and capture the output
    persistent_shell.stdin.write("pwd\n")
    persistent_shell.stdin.flush()
    persistent_shell.stdin.write("echo '__END_OF_DIRECTORY__'\n")
    persistent_shell.stdin.flush()

    current_directory = ""
    while True:
        line = persistent_shell.stdout.readline()
        if "__END_OF_DIRECTORY__" in line:
            break
        current_directory = line.strip()


def main_loop():
    global always_run, current_directory
    while True:
        get_current_directory()  # Update the current directory
        cmd = input(f"\n{current_directory}\n{get_concise_git_status()}dwim> ")
        if cmd == "exit":
            # Properly close the persistent shell before exiting
            persistent_shell.stdin.close()
            persistent_shell.terminate()
            persistent_shell.wait()
            break

        if cmd.strip() == "":
            continue

        cmd = get_dwim(cmd)

        if always_run:
            confirm = "y"
        else:
            confirm = input(f"Run '{cmd}'? [Y/n/always]: ") or "y"

        if confirm.lower() in ["y", "yes", ""]:
            run_command(cmd)
        elif confirm.lower() == "always":
            always_run = True
            run_command(cmd)
        else:
            print("Command skipped")


def main():
    print("Welcome to dwim (Do What I Mean)")
    print("Requires: OPENAI_API_KEY in environment."),

    start_persistent_shell()
    readline.set_completer(complete)
    readline.parse_and_bind("tab: complete")
    main_loop()


if __name__ == "__main__":
    main()
