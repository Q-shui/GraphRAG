import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const rows = fs.readFileSync(path.join(root, 'datasets', 'textbook_audit_view.jsonl'), 'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);
const wb = Workbook.create();
const s = wb.worksheets.add('审核总表');
const headers = ['题目ID','教材','章节','页码','知识点','题型','难度','题目','参考答案','关键得分点','证据核验状态','待解决问题','专家审核意见'];
s.getRange('A1:M1').values = [headers];
const data = rows.map(x => [x.question_id, x.source_ids.join(';'), x.chapter_id || x.evidence_locations.join(';'), x.evidence_locations.join(';'), x.knowledge_domain, x.primary_type, x.difficulty, x.question, x.reference_answer, x.key_answer_points.join('；'), x.evidence_status || 'REJECTED', x.rejection_reason ? `${x.rejection_reason}；重复题：${x.duplicate_of_question_id}` : (x.evidence_status === 'TEXTBOOK_VERIFIED' ? '已完成本轮页面视觉复核。' : 'OCR已完成，仍需逐页对照原扫描。'), '']);
if (data.length) s.getRange(`A2:M${data.length+1}`).values = data;
s.getRange('A1:M1').format = { fill: '#1F4E78', font: { bold: true, color: '#FFFFFF' } };
for (const [col,w] of Object.entries({A:12,B:12,C:22,D:18,E:15,F:8,G:8,H:42,I:42,J:36,K:18,L:48,M:25})) s.getRange(`${col}:${col}`).format.column_width = w;
const n = wb.worksheets.add('说明');
n.getRange('A1:B6').values = [
 ['项目','KQA-P8 教材题库第一阶段'],
 ['审核表状态','含16条新候选题和16条被拒绝的历史重复草题。'],
 ['证据状态','3条已页面核验；13条OCR后待逐页复核；16条历史重复题被拒绝。'],
 ['审计原则','不以历史工程经验题重新计入教材新题；不将章节标题当作教材正文证据。'],
 ['专家审核','空白，未冒充专家审核。'],
 ['下一步','启用受控OCR并人工核对原始页；先处理未覆盖章节。']
];
n.getRange('A1:B6').format.wrap_text = true;
n.getRange('A:A').format.column_width = 18; n.getRange('B:B').format.column_width = 100;
n.getRange('A1:A6').format = { fill: '#D9EAF7', font: { bold: true } };
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(path.join(root, 'review', 'P8_教材题库审核表.xlsx'));
