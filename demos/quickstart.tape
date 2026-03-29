Source demos/_settings.tape

Output demos/quickstart.gif
Output demos/quickstart.mp4

Hide
Type `eval "$(pixi shell-hook -s bash -e dev)"`
Enter
Wait /\)/
Type `export PS1="\[\033[1;32m\]$\[\033[0m\] "`
Enter
Wait /\$/
Type "rm -rf /tmp/my-project && mkdir -p /tmp/my-project && cd /tmp/my-project"
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Initialize a new workspace"
Enter
Sleep 500ms

Type@80ms "conda workspace init --name my-project"
Enter
Wait /\$/
Sleep 1s

Type "# Add some dependencies"
Enter
Sleep 500ms

Type@80ms `conda workspace add "python>=3.12" "numpy>=2"`
Enter
Wait /\$/
Sleep 1s

Type@80ms `conda workspace add -e test "pytest>=8.0"`
Enter
Wait /\$/
Sleep 1s

Type@80ms "bat -pp conda.toml"
Enter
Wait /\$/
Sleep 3s

Type "# Install all environments"
Enter
Sleep 500ms

Type@80ms "conda workspace install"
Enter
Wait /\$/
Sleep 2s

Type "# See what we built"
Enter
Sleep 500ms

Type@80ms "conda workspace envs"
Enter
Wait /\$/
Sleep 2s

Type "# Run a command in the test environment"
Enter
Sleep 500ms

Type@80ms `conda workspace shell -e test -- python -c "import numpy; print(numpy.__version__)"`
Enter
Wait /\$/
Sleep 3s
