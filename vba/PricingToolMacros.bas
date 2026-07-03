Attribute VB_Name = "PricingToolMacros"
Option Explicit

Sub RefreshPricingWorkbook()
    'Refreshes formulas and external query tables if they exist.
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    ThisWorkbook.RefreshAll
    Application.CalculateFullRebuild
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    MsgBox "Workbook refreshed. Note: this does not retrain Python unless you separately run the Python model.", vbInformation
End Sub

Sub ResetPricingInputs()
    'Resets the calculator to a reasonable base profile.
    With ThisWorkbook.Worksheets("Pricing Calculator")
        .Range("B5").Value = "30-39"
        .Range("B6").Value = "2-5"
        .Range("B7").Value = "50-59"
        .Range("B8").Value = "D"
        .Range("B9").Value = "Regular"
        .Range("B10").Value = "6-7"
        .Range("B11").Value = "501-1500"
        .Range("B15").Value = 0.04
        .Range("B16").Value = 0.3
        .Range("B17").Value = 0.65
        .Range("B18").Value = 0.03
        .Range("B19").Value = 0
    End With
    Application.CalculateFull
    MsgBox "Pricing inputs reset.", vbInformation
End Sub

Sub ExportPricingScenarioPDF()
    Dim outPath As String
    outPath = ThisWorkbook.Path & Application.PathSeparator & "freMTPL2_Pricing_Scenario_" & Format(Now, "yyyymmdd_hhnnss") & ".pdf"
    ThisWorkbook.Worksheets("Pricing Calculator").ExportAsFixedFormat Type:=xlTypePDF, Filename:=outPath
    MsgBox "Pricing scenario exported to: " & outPath, vbInformation
End Sub

Sub RunPythonModelThenRefresh()
    'Optional advanced macro. You must edit pythonExe and projectPath for your computer.
    'This macro is intentionally not enabled by default because Python paths differ across machines.
    Dim pythonExe As String
    Dim projectPath As String
    Dim cmd As String

    pythonExe = "python"  'Example: "C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe"
    projectPath = ThisWorkbook.Path & Application.PathSeparator & ".."

    cmd = "cmd /c cd /d " & Chr(34) & projectPath & Chr(34) & " && " & pythonExe & " python\real_auto_pricing_model.py --sample-size 100000 && " & pythonExe & " python\build_excel_tool.py"
    Shell cmd, vbNormalFocus
    MsgBox "Python run started in a shell window. After it finishes, reopen or refresh the generated workbook.", vbInformation
End Sub
