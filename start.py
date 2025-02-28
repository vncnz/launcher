import subprocess
import sys, os
import pathlib

my_env = os.environ.copy()
my_env["LIBGL_ALWAYS_SOFTWARE"] = "1"

def main():
    # Launch Alacritty with the --print-events flag
    process = subprocess.Popen(
        ['alacritty', '-T', 'alacritty launcher', '--print-events', '-e', 'python', str(pathlib.Path(__file__).parent.resolve().joinpath('launcher.py')) ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=my_env
    )

    try:
        # Read the stdout line by line
        for line in process.stdout:
            print(line, end='')  # Print the output for debugging purposes
            if 'Focused(false)' in line:
                print("Focus lost. Terminating Alacritty.")
                process.terminate()
                break

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        process.stdout.close()
        process.stderr.close()
        process.wait()

if __name__ == "__main__":
    main()
