' butterfly downloader launcher - hidden, admin, opens web console
'
' Args:
'   no-guard  Skip starting a new guard (used by guard self-heal restarts)
'
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("Shell.Application")
Set wshShell = CreateObject("WScript.Shell")
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' exe filename
EXE_NAME = ChrW(34676) & ChrW(34678) & ChrW(21495) & ChrW(19979) & ChrW(36733) & ChrW(21161) & ChrW(25163) & ".exe"

skipGuard = False
For i = 0 To WScript.Arguments.Count - 1
    If LCase(WScript.Arguments.Item(i)) = "no-guard" Then
        skipGuard = True
    End If
Next

Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set allProcs = wmi.ExecQuery("SELECT * FROM Win32_Process")
For Each p In allProcs
    If p.Name = EXE_NAME Then p.Terminate()
Next
WScript.Sleep 500

shell.ShellExecute scriptPath & "\" & EXE_NAME, "", scriptPath, "runas", 0
WScript.Sleep 5000

Set check = wmi.ExecQuery("SELECT * FROM Win32_Process")
procsAlive = False
For Each p In check
    If p.Name = EXE_NAME Then
        procsAlive = True
        Exit For
    End If
Next
If Not procsAlive Then
    If Not skipGuard Then
        MsgBox "butterfly downloader failed to start. Possible causes: UAC denied, or blocked by antivirus.", 48, "butterfly-downloader"
    End If
    WScript.Quit
End If

If Not skipGuard Then
    wshShell.Run "http://127.0.0.1:2025/console", 1, False
    guardRunning = False
    Set guardProcs = wmi.ExecQuery("SELECT * FROM Win32_Process WHERE Name='wscript.exe'")
    For Each gp In guardProcs
        If Not IsNull(gp.CommandLine) Then
            If InStr(LCase(gp.CommandLine), "guard.vbs") > 0 Then
                guardRunning = True
                Exit For
            End If
        End If
    Next
    If Not guardRunning Then
        wshShell.Run "wscript.exe """ & scriptPath & "\guard.vbs""", 0, False
    End If
End If
