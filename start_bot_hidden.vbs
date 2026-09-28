Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\agent"
WshShell.Run """C:\Users\user\python_embed\pythonw.exe"" main.py --bot", 0, False
Set WshShell = Nothing
