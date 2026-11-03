# Extract a provenance-preserving CSV from legacy XLS files opened read-only.
$ErrorActionPreference='Stop'
$source=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..\2020YFB1713603-001-电解铝跨工序能质耦合、工艺参数感知模型数据集\数据集实体文件')).Path
$out=Join-Path $PSScriptRoot '..\qa_smoke_test\daily_reports_raw_extract.csv'
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
$map=@{potno='槽号';ddate='时间';fhlcnt='氟化铝料量';aetime='效应时间';averagev='平均电压';setv='设置电压';aev='效应电压';workv='工作电压';setnb='设定NB';alcntzsl='出铝指示量';zf='噪声';aestatus='效应状态'}
$records=[System.Collections.Generic.List[object]]::new();$excel=New-Object -ComObject Excel.Application;$excel.Visible=$false;$excel.DisplayAlerts=$false
try {
  Get-ChildItem -LiteralPath $source -Filter '*.xls' | Sort-Object Name | ForEach-Object {
    $file=$_.Name; $book=$excel.Workbooks.Open($_.FullName,0,$true)
    try {
      $ws=$book.Worksheets.Item(1); $v=$ws.UsedRange.Value2; $h=@{}
      for($c=1;$c -le $ws.UsedRange.Columns.Count;$c++){ $n=[string]$v[1,$c]; if($map.ContainsKey($n)){$n=$map[$n]}; $h[$n]=$c }
      for($r=2;$r -le $ws.UsedRange.Rows.Count;$r++){
        $records.Add([pscustomobject]@{source_file=$file;source_row=$r;cell_id=$v[$r,$h['槽号']];record_date=$v[$r,$h['时间']];average_voltage=$v[$r,$h['平均电压']];working_voltage=$v[$r,$h['工作电压']]})
      }
    } finally { $book.Close($false) }
  }
  $records|Export-Csv -NoTypeInformation -Encoding utf8 -LiteralPath $out
} finally { $excel.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
