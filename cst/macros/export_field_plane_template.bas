' Export selected field monitor to CSV.
' Usage:
' 1) Open solved full_array project.
' 2) Update RESULT_TREE_ITEM and OUTPUT_CSV.
' 3) Run this macro.

Option Explicit

Private Const RESULT_TREE_ITEM As String = "2D/3D Results\E-Field\e-field (f=30) [1]"
Private Const OUTPUT_CSV As String = "V:\BaiduSyncdisk\Study\ShanghaiTech\202603_NFMHI_Reproduction\cst\results\array_sim\field_plane_30GHz_100mm.csv"

Sub Main()
    On Error GoTo ExportFailed

    SelectTreeItem RESULT_TREE_ITEM
    With ASCIIExport
        .Reset
        .FileName OUTPUT_CSV
        .SetFileType "csv"
        .SetCsvSeparator ","
        .Execute
    End With

    MsgBox "Field export finished: " & OUTPUT_CSV, vbInformation
    Exit Sub

ExportFailed:
    MsgBox "Export failed. Check RESULT_TREE_ITEM path and CST monitor availability." & vbCrLf & _
           "Configured path: " & RESULT_TREE_ITEM, vbCritical
End Sub
