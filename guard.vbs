' butterfly downloader - watchdog + auto clean
' Behavior:
'   1. WeChat alive but downloader dead -> auto restart via start.vbs
'   2. WeChat missing over 30s -> stop downloader + exit
'   3. Every 20s scan downloads for *.md without matching _cleaned.md
Dim wmi, shell, fso, scriptPath, wechatMissing, checkInterval, maxIdle
Dim cleanInterval, cleanTimer, lockFile, CLEAN_TAG, EXE_NAME
Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' _清洗版
CLEAN_TAG = "_" & ChrW(28165) & ChrW(27927) & ChrW(29256)
EXE_NAME = ChrW(34676) & ChrW(34678) & ChrW(21495) & ChrW(19979) & ChrW(36733) & ChrW(21161) & ChrW(25163) & ".exe"

wechatMissing = 0
checkInterval = 10
maxIdle = 30
cleanInterval = 20
cleanTimer = 0

Function HasPendingClean(folder)
    HasPendingClean = False
    If Not fso.FolderExists(folder) Then Exit Function
    Dim f, subF
    For Each f In fso.GetFolder(folder).Files
        If LCase(fso.GetExtensionName(f.Name)) = "md" Then
            If InStr(f.Name, CLEAN_TAG) = 0 Then
                Dim cleaned
                cleaned = fso.BuildPath(folder, fso.GetBaseName(f.Name) & CLEAN_TAG & ".md")
                If Not fso.FileExists(cleaned) Then
                    HasPendingClean = True
                    Exit Function
                End If
            End If
        End If
    Next
    For Each subF In fso.GetFolder(folder).SubFolders
        If HasPendingClean(subF.Path) Then
            HasPendingClean = True
            Exit Function
        End If
    Next
End Function

Do
    WScript.Sleep checkInterval * 1000

    Set wechatProcs = wmi.ExecQuery("SELECT * FROM Win32_Process WHERE Name='WeChat.exe' OR Name='Weixin.exe'")
    wechatAlive = (wechatProcs.Count > 0)

    downloaderAlive = False
    Set allProcs = wmi.ExecQuery("SELECT * FROM Win32_Process")
    For Each p In allProcs
        If p.Name = EXE_NAME Then
            downloaderAlive = True
            Exit For
        End If
    Next

    cleanTimer = cleanTimer + checkInterval
    If cleanTimer >= cleanInterval Then
        cleanTimer = 0
        lockFile = scriptPath & "\._processing.lock"

        If fso.FileExists(lockFile) Then
            Dim lockAge
            lockAge = DateDiff("s", fso.GetFile(lockFile).DateLastModified, Now)
            If lockAge > 300 Then
                fso.DeleteFile lockFile, True
            End If
        End If

        If Not fso.FileExists(lockFile) Then
            If HasPendingClean(scriptPath & "\downloads") Then
                fso.CreateTextFile(lockFile).Close
                shell.Run "cmd /c cd /d """ & scriptPath & """ & python clean.py & del /f /q """ & lockFile & """", 0, False
            End If
        End If
    End If

    If wechatAlive Then
        wechatMissing = 0
        If Not downloaderAlive Then
            shell.Run "wscript.exe """ & scriptPath & "\start.vbs"" no-guard", 0, False
            WScript.Sleep 8000
        End If
    Else
        wechatMissing = wechatMissing + checkInterval
        If wechatMissing >= maxIdle Then
            If downloaderAlive Then
                Set killProcs = wmi.ExecQuery("SELECT * FROM Win32_Process")
                For Each p In killProcs
                    If p.Name = EXE_NAME Then p.Terminate()
                Next
                WScript.Sleep 2000
            End If
            WScript.Quit
        End If
    End If
Loop
