# Requires Microsoft Excel installed locally.  Opens every source XLS in
# read-only mode and never invokes Save/SaveAs or changes workbook contents.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\2020YFB1713603-001-电解铝跨工序能质耦合、工艺参数感知模型数据集\数据集实体文件')).Path
$output = Join-Path $PSScriptRoot '..\sources\daily_xls_structural_audit.json'
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $reports = foreach ($file in Get-ChildItem -LiteralPath $root -Filter '*.xls' | Sort-Object Name) {
        $book = $excel.Workbooks.Open($file.FullName, 0, $true)
        try {
            $sheets = foreach ($sheet in $book.Worksheets) {
                $range = $sheet.UsedRange
                $values = $range.Value2
                $headers = foreach ($col in 1..$range.Columns.Count) { [string]$values[1, $col] }
                $rows = foreach ($row in 2..$range.Rows.Count) {
                    $rowValues = foreach ($col in 1..$range.Columns.Count) { $values[$row, $col] }
                    [PSCustomObject]@{ values = @($rowValues) }
                }
                $cellIndex = [Array]::IndexOf($headers, '槽号')
                if ($cellIndex -lt 0) { $cellIndex = [Array]::IndexOf($headers, 'potno') }
                $timeIndex = [Array]::IndexOf($headers, '时间')
                if ($timeIndex -lt 0) { $timeIndex = [Array]::IndexOf($headers, 'ddate') }
                $times = @()
                if ($timeIndex -ge 0) {
                    $times = @($rows | ForEach-Object {
                        try { [datetime]::Parse([string]$_.values[$timeIndex]) } catch { $null }
                    } | Where-Object { $null -ne $_ })
                }
                $cellIds = @()
                if ($cellIndex -ge 0) { $cellIds = @($rows | ForEach-Object { $_.values[$cellIndex] } | Where-Object { $null -ne $_ } | Sort-Object -Unique) }
                $distinctDays = @($times | Sort-Object -Unique)
                $gapDays = @()
                for ($i = 1; $i -lt $distinctDays.Count; $i++) {
                    $gap = ($distinctDays[$i] - $distinctDays[$i - 1]).Days
                    if ($gap -gt 1) { $gapDays += ($gap - 1) }
                }
                $rowStrings = $rows | ForEach-Object { $_.values -join [char]31 }
                $duplicateRows = @($rowStrings | Group-Object | Where-Object Count -gt 1 | ForEach-Object { $_.Count - 1 } | Measure-Object -Sum).Sum
                $missingByColumn = foreach ($col in 0..($headers.Count - 1)) {
                    @($rows | Where-Object { $null -eq $_.values[$col] -or $_.values[$col] -eq '' }).Count
                }
                [PSCustomObject]@{
                    sheet = $sheet.Name
                    rows_including_header = $range.Rows.Count
                    columns = $range.Columns.Count
                    headers = @($headers)
                    first_three_data_rows = @($rows | Select-Object -First 3)
                    cell_ids_from_row_values = @($cellIds)
                    time_min = if ($times.Count) { ($times | Measure-Object -Minimum).Minimum.ToString('yyyy-MM-dd') } else { $null }
                    time_max = if ($times.Count) { ($times | Measure-Object -Maximum).Maximum.ToString('yyyy-MM-dd') } else { $null }
                    distinct_record_days = $distinctDays.Count
                    missing_calendar_days_between_first_and_last = if ($gapDays.Count) { [int](($gapDays | Measure-Object -Sum).Sum) } else { 0 }
                    missing_by_column = @($missingByColumn)
                    exact_duplicate_data_rows = if ($null -eq $duplicateRows) { 0 } else { [int]$duplicateRows }
                }
            }
            [PSCustomObject]@{ file = $file.Name; bytes = $file.Length; sheets = @($sheets) }
        }
        finally { $book.Close($false) }
    }
    $payload = [PSCustomObject]@{
        generated_at_local = (Get-Date).ToString('o')
        source_directory = $root
        reports = @($reports)
    }
    $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $output -Encoding utf8
}
finally {
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
}
