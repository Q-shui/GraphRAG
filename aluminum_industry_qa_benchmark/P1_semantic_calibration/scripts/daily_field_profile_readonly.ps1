# Read-only numeric profile of the 21 raw daily-report XLS workbooks.
$ErrorActionPreference='Stop'
$source=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..\2020YFB1713603-001-电解铝跨工序能质耦合、工艺参数感知模型数据集\数据集实体文件')).Path
$out=Join-Path $PSScriptRoot '..\source_daily_field_profile.json'
$map=@{potno='槽号';ddate='时间';fhlcnt='氟化铝料量';aetime='效应时间';averagev='平均电压';setv='设置电压';aev='效应电压';workv='工作电压';setnb='设定NB';alcntzsl='出铝指示量';zf='噪声';aestatus='效应状态'}
$store=@{}
$excel=New-Object -ComObject Excel.Application; $excel.Visible=$false; $excel.DisplayAlerts=$false
try {
  Get-ChildItem -LiteralPath $source -Filter '*.xls' | Sort-Object Name | ForEach-Object {
    $book=$excel.Workbooks.Open($_.FullName,0,$true)
    try {$ws=$book.Worksheets.Item(1); $v=$ws.UsedRange.Value2; $n=$ws.UsedRange.Rows.Count; $m=$ws.UsedRange.Columns.Count
      $h=@(); for($c=1;$c -le $m;$c++){$name=[string]$v[1,$c];if($map.ContainsKey($name)){$name=$map[$name]};$h+=$name}
      for($c=1;$c -le $m;$c++){ $name=$h[$c-1];if(!$store.ContainsKey($name)){$store[$name]=[System.Collections.Generic.List[object]]::new()};for($r=2;$r -le $n;$r++){$store[$name].Add($v[$r,$c])} }
    } finally {$book.Close($false)}
  }
  $profiles=foreach($name in $store.Keys|Sort-Object){$x=@($store[$name]);$present=@($x|Where-Object{$null -ne $_ -and $_ -ne ''});$numeric=@($present|Where-Object{$_ -is [double] -or $_ -is [int]});[pscustomobject]@{field=$name;rows=$x.Count;missing=$x.Count-$present.Count;numeric_count=$numeric.Count;non_numeric_count=$present.Count-$numeric.Count;minimum=if($numeric.Count){($numeric|Measure-Object -Minimum).Minimum}else{$null};maximum=if($numeric.Count){($numeric|Measure-Object -Maximum).Maximum}else{$null};examples=@($present|Select-Object -First 3)}}
  [pscustomobject]@{source=$source;generated_at=(Get-Date).ToString('o');profiles=@($profiles)}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $out -Encoding utf8
}finally{$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
