Source demos/_settings.tape

Output demos/shell.gif
Output demos/shell.mp4

Hide
Type `eval "$(pixi shell-hook -s bash -e dev)"`
Enter
Wait /\)/
Type `export PS1="\[\033[1;32m\]$\[\033[0m\] "`
Enter
Wait /\$/
Type `FIXTURES=$(pwd)/demos/fixtures`
Enter
Wait /\$/
Type "rm -rf /tmp/shell-demo && mkdir -p /tmp/shell-demo && cd /tmp/shell-demo"
Enter
Wait /\$/
Type `cp "$FIXTURES/shell.toml" conda.toml`
Enter
Wait /\$/
Type "conda workspace install"
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Drop into an interactive shell"
Enter
Sleep 500ms

Type@80ms "conda workspace shell -e default"
Hide
Enter
Wait /\$/
Type `export PS1="\[\033[1;32m\](default) $\[\033[0m\] "`
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type@80ms "python --version"
Enter
Wait /\$/
Sleep 1s

Type@80ms "which python"
Enter
Wait /\$/
Sleep 2s

Type@80ms "exit"
Enter
Wait /\$/
Sleep 1s

Type "# Or run a one-shot command"
Enter
Sleep 500ms

Type@80ms `conda workspace shell -e default -- python -c "print('Hello from the workspace!')"`
Enter
Wait /\$/
Sleep 3s
