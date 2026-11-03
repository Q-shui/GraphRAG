import fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
const root=fileURLToPath(new URL('..',import.meta.url));
const rows=JSON.parse(await fs.readFile(`${root}/review/reviewer_rows.json`,'utf8'));
const out=`${root}/review`;
const cols=['question_id','priority','knowledge_domain','question','reference_answer','key_answer_points','evidence_location','applicability','factual_correctness_review','evidence_sufficiency_review','condition_review','question_clarity_review','rubric_review','decision','revision_notes'];
async function make(name, role){
 const wb=Workbook.create(); const s=wb.worksheets.add('Review'); s.showGridLines=false;
 s.getRange('A1:O1').merge(); s.getRange('A1').values=[[`KQA-P5.2 ${role} expert review form`]];
 s.getRange('A2').values=[['Instructions: independently complete only columns I:O. Leave blank when evidence is insufficient; do not infer a review conclusion from priority.']];
 s.getRange('A4:O4').values=[cols.map(x=>x.replaceAll('_',' '))];
 s.getRange('A5').write(rows.map(r=>cols.map(c=>r[c]??'')));
 s.getRange(`A1:O1`).format={fill:'#1F4E78',font:{bold:true,color:'#FFFFFF',size:14},horizontalAlignment:'center'};
 s.getRange('A2:O2').format={font:{italic:true,color:'#595959'},wrapText:true};
 s.getRange('A4:O4').format={fill:'#D9EAF7',font:{bold:true},wrapText:true};
 s.getRange(`A4:O${4+rows.length}`).format.borders={preset:'all',style:'thin',color:'#D9D9D9'};
 s.getRange(`A5:H${4+rows.length}`).format.wrapText=true; s.getRange(`I5:O${4+rows.length}`).format.fill='#FFF2CC';
 s.getRange(`I5:M${4+rows.length}`).dataValidation={rule:{type:'list',values:['Correct','Minor issue','Major issue','Insufficient evidence','Not assessed']}};
 s.getRange(`N5:N${4+rows.length}`).dataValidation={rule:{type:'list',values:['RETAIN','REVISE','HOLD','REJECT','Refer to arbitration']}};
 s.freezePanes.freezeRows(4); s.getRange(`A1:O${4+rows.length}`).format.autofitColumns();
 ['A','B','C','I','J','K','L','M','N'].forEach(c=>s.getRange(`${c}:${c}`).format.columnWidth=16);
 ['D','E','F','G','H','O'].forEach(c=>s.getRange(`${c}:${c}`).format.columnWidth=32);
 wb.recalculate(); const x=await SpreadsheetFile.exportXlsx(wb); await x.save(`${out}/${name}`);
}
await make('reviewer_A.xlsx','Reviewer A'); await make('reviewer_B.xlsx','Reviewer B');
const wb=Workbook.create(); const s=wb.worksheets.add('Adjudication'); s.getRange('A1:H1').values=[['question_id','Reviewer A decision','Reviewer B decision','agreement','arbitration decision','rationale','item version','final status']]; s.getRange('A2').write(rows.map(r=>[r.question_id,'','','','','','', 'Not-Reviewed'])); s.getRange(`A1:H${rows.length+1}`).format.borders={preset:'all',style:'thin',color:'#D9D9D9'}; s.getRange('A1:H1').format={fill:'#1F4E78',font:{bold:true,color:'#FFFFFF'}}; s.getRange(`B2:E${rows.length+1}`).dataValidation={rule:{type:'list',values:['RETAIN','REVISE','HOLD','REJECT','Not assessed']}}; s.freezePanes.freezeRows(1); s.getRange(`A1:H${rows.length+1}`).format.autofitColumns(); wb.recalculate(); const x=await SpreadsheetFile.exportXlsx(wb); await x.save(`${out}/adjudication.xlsx`);
