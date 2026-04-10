' Import 60x60 height matrix CSV and build dielectric pillar array.
' Usage:
' 1) Open your full_array CST project.
' 2) Update USER CONFIG constants below.
' 3) Run this macro from Macro -> Macros.

Option Explicit

Private Const CSV_PATH As String = "V:\BaiduSyncdisk\Study\ShanghaiTech\202603_NFMHI_Reproduction\python\outputs\height_maps\height_matrix.csv"
Private Const N_ROWS As Long = 60
Private Const N_COLS As Long = 60
Private Const CELL_SIZE_MM As Double = 5#
Private Const BASE_Z_MM As Double = 0#
Private Const COMPONENT_NAME As String = "array"
Private Const MATERIAL_NAME As String = "VeroWhitePlus"
Private Const NAME_PREFIX As String = "cell_"

Sub Main()
    Dim heights() As Double
    heights = LoadHeightCsv(CSV_PATH, N_ROWS, N_COLS)

    BuildArrayFromHeights heights, N_ROWS, N_COLS
    Rebuild
    MsgBox "Height matrix import completed: " & CStr(N_ROWS) & "x" & CStr(N_COLS), vbInformation
End Sub

Private Function LoadHeightCsv(ByVal csvPath As String, ByVal nRows As Long, ByVal nCols As Long) As Double()
    Dim vals() As Double
    ReDim vals(0 To nRows - 1, 0 To nCols - 1)

    Dim f As Integer
    f = FreeFile
    Open csvPath For Input As #f

    Dim r As Long
    r = 0
    Do While Not EOF(f) And r < nRows
        Dim lineText As String
        Line Input #f, lineText
        lineText = Trim$(lineText)

        If Len(lineText) > 0 Then
            Dim tokens() As String
            tokens = Split(lineText, ",")

            Dim c As Long
            For c = 0 To nCols - 1
                If c <= UBound(tokens) Then
                    vals(r, c) = CDbl(Trim$(tokens(c)))
                Else
                    vals(r, c) = 0#
                End If
            Next c
            r = r + 1
        End If
    Loop
    Close #f

    If r <> nRows Then
        MsgBox "Warning: CSV row count = " & CStr(r) & ", expected = " & CStr(nRows), vbExclamation
    End If

    LoadHeightCsv = vals
End Function

Private Sub BuildArrayFromHeights(ByRef h() As Double, ByVal nRows As Long, ByVal nCols As Long)
    Dim rowIdx As Long, colIdx As Long
    For rowIdx = 0 To nRows - 1
        For colIdx = 0 To nCols - 1
            Dim x1 As Double, x2 As Double, y1 As Double, y2 As Double, z2 As Double
            x1 = colIdx * CELL_SIZE_MM
            x2 = x1 + CELL_SIZE_MM
            y1 = rowIdx * CELL_SIZE_MM
            y2 = y1 + CELL_SIZE_MM
            z2 = BASE_Z_MM + h(rowIdx, colIdx)

            Dim objName As String
            objName = NAME_PREFIX & CStr(rowIdx + 1) & "_" & CStr(colIdx + 1)
            CreateBrick objName, x1, x2, y1, y2, BASE_Z_MM, z2
        Next colIdx
    Next rowIdx
End Sub

Private Sub CreateBrick(ByVal name As String, ByVal x1 As Double, ByVal x2 As Double, _
                        ByVal y1 As Double, ByVal y2 As Double, ByVal z1 As Double, ByVal z2 As Double)
    If z2 <= z1 Then
        Exit Sub
    End If

    With Brick
        .Reset
        .Name name
        .Component COMPONENT_NAME
        .Material MATERIAL_NAME
        .Xrange CStr(x1), CStr(x2)
        .Yrange CStr(y1), CStr(y2)
        .Zrange CStr(z1), CStr(z2)
        .Create
    End With
End Sub
