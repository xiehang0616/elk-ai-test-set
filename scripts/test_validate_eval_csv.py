"""Regression checks for generic CSV contracts."""
import unittest
from validate_eval_csv import COLUMNS, validate


class EvaluationValidation(unittest.TestCase):
    def result(self, rows, kind='workbench', **kwargs):
        return validate(COLUMNS[kind], rows, kind, **kwargs)[0]

    def scored(self, method='二值'):
        r=dict.fromkeys(COLUMNS['workbench'],'')
        r.update({'case_id':'C1','run_id':'RUN1','评审者':'A','metric_id':'QUALITY',
                  '评分方式':method,'候选版本':'v2','候选输出':'answer',
                  '候选评分':'通过' if method=='二值' else '4',
                  '候选硬门槛':'不适用','规则编号':'R-1','输出证据':'line 1',
                  '样本问题':'无','评测状态':'已评分'})
        if method=='GSB':
            r.update({'候选评分':'','GSB':'G','基线版本':'v1','基线输出':'baseline','基线硬门槛':'通过'})
        return r

    def test_all_methods(self):
        for method in ('二值','1-5','GSB'):
            self.assertFalse(self.result([self.scored(method)]))

    def test_missing_pair(self):
        r=self.scored('GSB');r['基线输出']=''
        self.assertTrue(self.result([r]))

    def test_score_range(self):
        for value in ('abc','0','6','3.5'):
            r=self.scored('1-5');r['候选评分']=value
            self.assertTrue(self.result([r]))

    def test_missing_gate_or_evidence(self):
        for col in ('候选硬门槛','规则编号','输出证据'):
            r=self.scored();r[col]=''
            self.assertTrue(self.result([r]))

    def test_initial_and_empty(self):
        r=self.scored()
        self.assertTrue(self.result([r],initial=True))
        for col in COLUMNS['workbench'][7:]:r[col]=''
        self.assertFalse(self.result([r],initial=True))
        self.assertTrue(self.result([]))
        self.assertFalse(self.result([],allow_empty=True))

    def test_na_and_issue(self):
        r=self.scored();r['评测状态']='不适用'
        self.assertTrue(self.result([r]))
        r['候选评分']='';r['候选硬门槛']=''
        self.assertFalse(self.result([r]))
        r['评测状态']='样本待修订';r['样本问题']='标准问题'
        self.assertFalse(self.result([r]))
        r['评测状态']='已评分'
        self.assertTrue(self.result([r]))

    def test_identity_and_run_scope(self):
        r=self.scored();other=dict(r)
        self.assertTrue(self.result([r,other]))
        other['metric_id']='SECOND';other['候选输出']='changed'
        self.assertTrue(self.result([r,other]))
        other['候选输出']=r['候选输出'];other['run_id']='RUN2'
        self.assertTrue(self.result([r,other]))

    def test_generic_coverage_and_ragged_rows(self):
        r=dict.fromkeys(COLUMNS['dataset'],'value')
        r.update({'难度':'低','样本类型':'对抗/高风险','metric_ids':'任务完成;证据质量'})
        self.assertFalse(self.result([r],kind='dataset',metrics=['任务完成','证据质量'],minimum=1))
        self.assertTrue(self.result([r],kind='dataset',metrics=['任务完成','缺失指标'],minimum=1))
        r['备注']=None
        self.assertTrue(self.result([r],kind='dataset'))

    def test_hard_failure_can_be_recorded_without_claiming_success(self):
        r=self.scored();r['候选硬门槛']='不通过';r['候选评分']='不通过'
        self.assertFalse(self.result([r]))
        r['评测状态']='通过'
        self.assertTrue(self.result([r]))


if __name__=='__main__':unittest.main()
