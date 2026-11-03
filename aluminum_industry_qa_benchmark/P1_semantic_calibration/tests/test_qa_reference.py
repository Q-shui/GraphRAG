import sys, tempfile, csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import qa_reference_calculator as q

def expect(code, fn):
 try: fn()
 except q.QAError as e: assert e.code==code
 else: raise AssertionError('expected '+code)
def row(day='2020-01-01',value='4.0',work='4.1'):
 return {'source_file':'a.xls','source_row':2,'cell_id':1,'record_date':q._date(day),'average_voltage':q._number(value),'working_voltage':q._number(work)}
def main():
 rs=q.load(); got=q.calculate_statistics(rs,2726,'2017-06-23','2017-06-30','average_voltage'); assert abs(got['mean']-4.249375)<1e-12
 expect('E_NO_RECORDS',lambda:q.calculate_statistics(rs,9999,'2017-06-23','2017-06-30','average_voltage'))
 expect('E_INVALID_BOUNDS',lambda:q.calculate_statistics(rs,2726,'2017-06-30','2017-06-23','average_voltage'))
 expect('E_UNSUPPORTED_FIELD',lambda:q.calculate_statistics(rs,2726,'2017-06-23','2017-06-30','noise'))
 expect('E_INVALID_TYPE',lambda:q.calculate_statistics(rs,'2726','2017-06-23','2017-06-30','average_voltage'))
 dup=[row(),dict(row(),source_row=3)]; s=q.calculate_statistics(dup,1,'2020-01-01','2020-01-01','average_voltage'); assert s['duplicates_removed']==1 and s['valid_record_count']==1
 conflict=dict(row(),source_row=3); conflict['average_voltage']=5.0
 expect('E_CONFLICTING_RECORDS',lambda:q.calculate_statistics([row(),conflict],1,'2020-01-01','2020-01-01','average_voltage'))
 expect('E_NO_VALID_VALUES',lambda:q.calculate_statistics([row(value='')],1,'2020-01-01','2020-01-01','average_voltage'))
 print('PASS: regression, empty/nonexistent, boundaries, field/type, duplicate, conflict, null')
if __name__=='__main__':main()
