Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\agent"
WshShell.Run "python main.py --daemon", 0, False
Set WshShell = Nothing
