' auto_start.vbs - auto-start at boot, silent launch + guard
' Put a shortcut in shell:startup (Win+R -> shell:startup)
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("Shell.Application")
Set wshShell = CreateObject("WScript.Shell")
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' exe filename
EXE_NAME = ChrW(34676) & ChrW(34678) & ChrW(21495) & ChrW(19979) & ChrW(36733) & ChrW(21161) & ChrW(25163) & ".exe"

' skip if already running
Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set allProcs = wmi.ExecQuery("SELECT * FROM Win32_Process")
alreadyRunning = False
For Each p In allProcs
    If p.Name = EXE_NAME Then
        alreadyRunning = True
        Exit For
    End If
Next
If alreadyRunning Then
    WScript.Quit
End If

' launch downloader (silent, admin)
shell.ShellExecute scriptPath & "\" & EXE_NAME, "", scriptPath, "runas", 0

' wait for startup
WScript.Sleep 5000

' launch guard (post-process)
wshShell.Run "wscript.exe """ & scriptPath & "\guard.vbs""", 0, False
