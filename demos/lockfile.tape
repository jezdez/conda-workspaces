Source demos/_settings.tape

Output demos/lockfile.gif
Output demos/lockfile.mp4

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
Type "rm -rf /tmp/lockfile-demo && mkdir -p /tmp/lockfile-demo && cd /tmp/lockfile-demo"
Enter
Wait /\$/
Type `cp "$FIXTURES/lockfile.toml" conda.toml`
Enter
Wait /\$/
Type "clear"
Enter
Wait /\$/
Show

Type "# Install and solve dependencies"
Enter
Sleep 500ms

Type@80ms "conda workspace install"
Enter
Wait /\$/
Sleep 2s

Type "# Generate a lockfile for reproducible installs"
Enter
Sleep 500ms

Type@80ms "conda workspace lock"
Enter
Wait /\$/
Sleep 2s

Type@80ms "head -20 conda.lock"
Enter
Wait /\$/
Sleep 3s

Type "# Clean and reinstall from lock — no solving needed"
Enter
Sleep 500ms

Type@80ms "conda workspace clean --yes"
Enter
Wait /\$/
Sleep 1s

Type@80ms "conda workspace install --locked"
Enter
Wait /\$/
Sleep 3s
