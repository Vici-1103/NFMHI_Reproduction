' Build a 60x60 full-array CST project from a height CSV.
' Usage:
' 1) Open CST Studio Suite and create a new empty MW Studio project.
' 2) Open Macros -> Edit Macros, import this BAS file, and update CSV_PATH only.
' 3) Run the macro. It will configure the project, create the material, add the monitor, and build the full array.

Option Explicit

' =========================
' USER CONFIG
' =========================
Private Const CSV_PATH As String = "D:\work\NFMHI_Reproduction\python\outputs\height_maps\height_matrix.csv"
Private Const N_ROWS As Long = 60
Private Const N_COLS As Long = 60
Private Const CELL_SIZE_MM As Double = 5#
Private Const HMIN_MM As Double = 2#
Private Const HMAX_MM As Double = 8#
Private Const FREQ_GHZ As Double = 30#
Private Const FREQ_MIN_GHZ As Double = 29#
Private Const FREQ_MAX_GHZ As Double = 31#
Private Const MONITOR_Z_MM As Double = 102#

Private Const COMPONENT_NAME As String = "array"
Private Const MATERIAL_NAME As String = "VeroWhitePlus"
Private Const NAME_PREFIX As String = "cell_"
Private Const EPSILON_R As Double = 2.802
Private Const MU_R As Double = 1#
Private Const TAN_DELTA As Double = 0.0357

Sub Main()
    Dim heights() As Double
    If Not CsvExists(CSV_PATH) Then
        MsgBox "CSV file not found: " & CSV_PATH, vbCritical
        Exit Sub
    End If

    heights = LoadHeightCsv(CSV_PATH, N_ROWS, N_COLS)

    If Not HeightRangeIsValid(heights, N_ROWS, N_COLS) Then
        MsgBox "Height matrix contains values outside the configured range [" & CStr(HMIN_MM) & ", " & CStr(HMAX_MM) & "] mm.", vbCritical
        Exit Sub
    End If

    If Not ConfigureProject() Then
        Exit Sub
    End If
    If Not CreateOrUpdateMaterial() Then
        Exit Sub
    End If
    BuildArrayFromHeights heights, N_ROWS, N_COLS

    MsgBox "Full-array build completed: " & CStr(N_ROWS) & "x" & CStr(N_COLS), vbInformation
End Sub

Private Function ConfigureProject() As Boolean
    On Error GoTo Failed
    With Units
        .Geometry "mm"
        .Frequency "GHz"
        .Time "ns"
    End With

    With Background
        .ResetBackground
        .Type "Normal"
        .Epsilon "1.0"
        .Mu "1.0"
        .XminSpace "0.0"
        .XmaxSpace "0.0"
        .YminSpace "0.0"
        .YmaxSpace "0.0"
        .ZminSpace "0.0"
        .ZmaxSpace "0.0"
    End With

    With Boundary
        .Xmin "expanded open"
        .Xmax "expanded open"
        .Ymin "expanded open"
        .Ymax "expanded open"
        .Zmin "expanded open"
        .Zmax "expanded open"
        .Xsymmetry "none"
        .Ysymmetry "none"
        .Zsymmetry "none"
    End With

    With Solver
        .FrequencyRange CStr(FREQ_MIN_GHZ), CStr(FREQ_MAX_GHZ)
    End With

    With PlaneWave
        .Reset
        .Normal "0", "0", "-1"
        .EVector "1", "0", "0"
        .Polarization "Linear"
        .SetUserDecouplingPlane "False"
        .Store
    End With

    With Monitor
        .Reset
        .Name BuildMonitorName()
        .Domain "Frequency"
        .FieldType "Efield"
        .Frequency CStr(FREQ_GHZ)
        .PlaneNormal "z"
        .PlanePosition CStr(MONITOR_Z_MM)
        .Create
    End With

    ConfigureProject = True
    Exit Function

Failed:
    MsgBox "Failed to configure the CST project: " & Err.Description, vbCritical
    ConfigureProject = False
End Function

Private Function CreateOrUpdateMaterial() As Boolean
    On Error GoTo Failed

    With Material
        .Reset
        .Name MATERIAL_NAME
        .Folder ""
        .Type "Normal"
        .FrqType "all"
        .MaterialUnit "Frequency", "GHz"
        .MaterialUnit "Geometry", "mm"
        .MaterialUnit "Time", "ns"
        .Epsilon CStr(EPSILON_R)
        .Mue CStr(MU_R)
        .TanD CStr(TAN_DELTA)
        .TanDGiven "True"
        .TanDModel "ConstTanD"
        .Create
    End With

    CreateOrUpdateMaterial = True
    Exit Function

Failed:
    MsgBox "Failed to create material " & MATERIAL_NAME & ": " & Err.Description, vbCritical
    CreateOrUpdateMaterial = False
End Function

Private Function CsvExists(ByVal csvPath As String) As Boolean
    CsvExists = (Len(Dir$(csvPath)) > 0)
End Function

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
            If UBound(tokens) - LBound(tokens) + 1 <> nCols Then
                Close #f
                MsgBox "CSV column count mismatch on row " & CStr(r + 1) & ". Expected " & CStr(nCols) & " columns.", vbCritical
                End
            End If

            Dim c As Long
            For c = 0 To nCols - 1
                vals(r, c) = CDbl(Trim$(tokens(c)))
            Next c

            r = r + 1
        End If
    Loop

    Do While Not EOF(f)
        Dim extraLine As String
        Line Input #f, extraLine
        If Len(Trim$(extraLine)) > 0 Then
            Close #f
            MsgBox "CSV has more than " & CStr(nRows) & " non-empty rows.", vbCritical
            End
        End If
    Loop

    Close #f

    If r <> nRows Then
        MsgBox "CSV row count = " & CStr(r) & ", expected = " & CStr(nRows), vbCritical
        End
    End If

    LoadHeightCsv = vals
End Function

Private Function BuildMonitorName() As String
    BuildMonitorName = "e-field (f=" & CStr(FREQ_GHZ) & ";z=" & CStr(MONITOR_Z_MM) & ")"
End Function

Private Function HeightRangeIsValid(ByRef h() As Double, ByVal nRows As Long, ByVal nCols As Long) As Boolean
    Dim rowIdx As Long
    Dim colIdx As Long

    HeightRangeIsValid = True
    For rowIdx = 0 To nRows - 1
        For colIdx = 0 To nCols - 1
            If h(rowIdx, colIdx) < HMIN_MM Or h(rowIdx, colIdx) > HMAX_MM Then
                HeightRangeIsValid = False
                Exit Function
            End If
        Next colIdx
    Next rowIdx
End Function

Private Sub BuildArrayFromHeights(ByRef h() As Double, ByVal nRows As Long, ByVal nCols As Long)
    Dim rowIdx As Long
    Dim colIdx As Long

    For rowIdx = 0 To nRows - 1
        For colIdx = 0 To nCols - 1
            Dim x1 As Double, x2 As Double, y1 As Double, y2 As Double, z2 As Double
            x1 = colIdx * CELL_SIZE_MM
            x2 = x1 + CELL_SIZE_MM
            y1 = rowIdx * CELL_SIZE_MM
            y2 = y1 + CELL_SIZE_MM
            z2 = h(rowIdx, colIdx)

            CreateBrick NAME_PREFIX & CStr(rowIdx + 1) & "_" & CStr(colIdx + 1), x1, x2, y1, y2, 0#, z2
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
