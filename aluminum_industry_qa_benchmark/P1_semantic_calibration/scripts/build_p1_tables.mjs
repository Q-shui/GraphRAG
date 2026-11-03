import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
const root=process.cwd(); const out=`${root}/aluminum_industry_qa_benchmark/P1_semantic_calibration`;
const profile=JSON.parse(await fs.readFile(`${out}/source_daily_field_profile.json`,'utf8')).profiles;
const p=Object.fromEntries(profile.map(x=>[x.field,x]));
const fields=['槽号','时间','氟化铝料量','效应时间','平均电压','设置电压','效应电压','工作电压','设定NB','出铝指示量','噪声','效应状态'];
const role={槽号:'设备标识；直接记录',时间:'日报日期；物理时点确认、可用时点未知',氟化铝料量:'名称提示下料相关量；厂方口径未证实',效应时间:'名称提示效应持续相关量；厂方口径未证实',平均电压:'日报聚合电压候选；窗口/单位/延迟待确认',设置电压:'名称提示设定值；是否实际执行未知',效应电压:'名称提示效应期间电压；口径待确认',工作电压:'日报聚合电压候选；窗口/单位/延迟待确认',设定NB:'含义未映射',出铝指示量:'指示量，不可等同实际出铝量',噪声:'名称不足以确定测量对象或算法',效应状态:'数值状态码，代码本缺失'};
const grade={槽号:'A',时间:'B',平均电压:'B',工作电压:'B'};
const use={槽号:'允许：筛选/分组',时间:'允许：回顾性窗口；禁止推断导出时点',平均电压:'附条件允许：回顾性查询/统计',工作电压:'附条件允许：回顾性查询/统计'};
const rows=fields.map(f=>[f,'21份电解槽日报/*.xls, Sheet1',f==='时间'?'日期文本':'数值',p[f]?.missing??0,`${p[f]?.minimum??'—'} 至 ${p[f]?.maximum??'—'}`,role[f], '未知/待厂方确认','未知/待厂方确认',grade[f]||'C',use[f]||'禁止作为金标准工程解释；仅可原始值查询（字段名）','单位、统计窗口、生成/导出时点、是否事后修订']);
async function book(name, headers, data){const wb=Workbook.create();const s=wb.worksheets.add('总表');s.getRangeByIndexes(0,0,1,headers.length).values=[headers];s.getRangeByIndexes(1,0,data.length,headers.length).values=data;s.freezePanes.freezeRows(1);s.getRange(`A1:${String.fromCharCode(64+headers.length)}1`).format={fill:'#1F4E78',font:{bold:true,color:'#FFFFFF'},wrapText:true};s.getUsedRange().format.wrapText=true;s.getUsedRange().format.autofitColumns();s.getUsedRange().format.autofitRows();s.getRange(`A1:${String.fromCharCode(64+headers.length)}${data.length+1}`).format.borders={preset:'all',style:'thin',color:'#D9E2F3'};wb.recalculate();const x=await SpreadsheetFile.exportXlsx(wb);await x.save(`${out}/${name}`);}
await book('02_12字段语义与证据总表.xlsx',['原始字段','来源','值类型','空值数','实际值域','工程含义/边界','统计窗口/单位','生成与可用时点','证据等级','问答适用性','待确认问题'],rows);
const know=fields.map(f=>[f, (f==='平均电压'||f==='工作电压')?'《现代铝电解》14 参数测量、21 控制系统、27 槽况综合分析':(f==='氟化铝料量'?'《现代铝电解》25 电解质摩尔比控制':'相关教材章节待页级核验'), '仅章节级目录证据；未OCR页级摘录','E：暂不可作金标准知识证据','需OCR+人工定位页码']);
await book('04_教材证据映射表.xlsx',['日报字段','候选教材章节','证据现状','知识用途状态','下一步'],know);
