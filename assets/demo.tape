Output assets/demo.gif

Set FontSize 15
Set Width 1000
Set Height 560
Set Theme "Dracula"
Set Padding 16
Set TypingSpeed 60ms
Set CursorBlink false

Hide
Type "clear"
Enter
Show
Sleep 500ms

Type "python3 main.py init chan --file-cap 64"
Enter
Sleep 1s

Type "python3 main.py shell"
Enter
Sleep 500ms

Type "mkdir -p projects/demo"
Enter
Sleep 300ms

Type "write projects/demo/todo.txt 'buy milk | record sfs demo'"
Enter
Sleep 300ms

Type "cat projects/demo/todo.txt"
Enter
Sleep 500ms

Type "cd projects/demo"
Enter
Sleep 300ms

Type "pwd"
Enter
Sleep 300ms

Type "ls"
Enter
Sleep 300ms

Type "grep demo"
Enter
Sleep 500ms

Type "write big.txt 0123456789012345678901234567890123456789012345678901234567890123456789"
Enter
Sleep 700ms

Type "tree"
Enter
Sleep 900ms

Type "exit"
Enter
Sleep 400ms

Type "python3 main.py tree"
Enter
Sleep 2s
