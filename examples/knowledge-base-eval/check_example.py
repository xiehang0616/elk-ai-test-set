import csv
from collections import Counter
from pathlib import Path

root=Path(__file__).resolve().parent
def read(name):
    with (root/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
data=read('dataset.csv');standards=read('standard.csv');work=read('workbench.csv');summary=read('summary.csv')
assert Counter(r['样本类型'] for r in data)=={'常规':5,'复杂':3,'边界':2,'对抗/高风险':2}
expected={(r['case_id'],m) for r in data for m in r['metric_ids'].split(';')}
assert expected=={(r['case_id'],r['metric_id']) for r in work}
assert len(expected)==len(work)==36
methods={r['metric_id']:r['评分方式'] for r in standards}
assert all(methods[r['metric_id']]==r['评分方式'] for r in work)
assert all((root / r['参考材料'].split(' #')[0]).is_file() for r in data)
pending=[r for r in work if r['评测状态']=='待输出']
assert len(pending)==3 and all(r['case_id']=='SIM-012' for r in pending)
assert all(r['基线输出'] and not r['候选输出'] and not any(r[k] for k in ['基线评分','候选评分','GSB','基线硬门槛','候选硬门槛']) for r in pending)
assert {r['case_id'] for r in work if r['候选硬门槛']=='不通过'}=={'SIM-011'}
assert all(r['metric_id']=='M1' for r in work if r['候选硬门槛']=='不通过')
assert all(r['样本问题']=='无' for r in work if r['评测状态']=='已评分')
assert Counter(r['GSB'] for r in work if r['metric_id']=='M3' and r['评测状态']=='已评分')=={'G':7,'S':2,'B':2}
assert sum(int(r['候选评分']) for r in work if r['metric_id']=='M2' and r['评测状态']=='已评分')==52
assert sum(r['候选评分']=='通过' for r in work if r['metric_id']=='M1')==10
assert [r['已评分数'] for r in summary]==['11']*3
print('PASS: 跨表关联、矩阵计数、材料路径、缺失状态、唯一门槛归属及参考汇总均一致。')
