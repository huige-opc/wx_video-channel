' stop.vbs - stop the butterfly downloader (kill guard first, then exe)
Set fso   = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("Shell.Application")
Set wmi   = GetObject("winmgmts:\\.\root\cimv2")

' exe filename
EXE_NAME = ChrW(34676) & ChrW(34678) & ChrW(21495) & ChrW(19979) & ChrW(36733) & ChrW(21161) & ChrW(25163) & ".exe"

' 1. kill guard.vbs first
Set guardProcs = wmi.ExecQuery("SELECT * FROM Win32_Process WHERE Name='wscript.exe'")
For Each gp In guardProcs
    If Not IsNull(gp.CommandLine) Then
        If InStr(LCase(gp.CommandLine), "guard.vbs") > 0 Then
            gp.Terminate()
        End If
    End If
Next

WScript.Sleep 500

' 2. kill the main exe (admin required)
shell.ShellExecute "cmd.exe", "/c taskkill /F /IM " & EXE_NAME & " /T", "", "runas", 0
