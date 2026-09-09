#!/usr/bin/env python3
"""Validate generic evaluation CSVs; business semantics require human review."""
from __future__ import annotations
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / 'assets/schema.json').read_text())
COLUMNS = SCHEMA['sheets']
ENUMS = SCHEMA['enums']


def metric_ids(value):
    return [part.strip() for part in value.split(';') if part.strip()]


def validate(headers, rows, kind, initial=False, metrics=None, minimum=5, expected=None, allow_empty=False):
    errors, warnings = [], []
    if headers != COLUMNS[kind]:
        return ['字段名称或顺序与 assets/schema.json 不一致'], []
    if not rows and not allow_empty:
        errors.append('没有数据行；空模板需显式使用 --allow-empty')
    if expected is not None and len(rows) != expected:
        errors.append(f'实际 {len(rows)} 行，不等于要求的 {expected} 行')
    clean = []
    for i, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            errors.append(f'第 {i} 行字段数量与表头不同')
        clean.append({key: str(row.get(key) or '').strip() for key in headers})
    rows = clean
    required = {'dataset': COLUMNS[kind][:10] if kind == 'dataset' else [],
                'workbench': ['case_id', 'run_id', '评审者', 'metric_id', '评分方式', '候选版本'],
                'standard': COLUMNS['standard'], 'summary': ['metric_id', '评分方式']}[kind]
    seen = set()
    output_by_case = {}
    for i, row in enumerate(rows, 2):
        def fail(message):
            errors.append(f'第 {i} 行：{message}')
        for col in required:
            if not row[col]:
                fail(f'{col} 为空')
        for col in ('难度', '样本类型', '评分方式', '样本问题', '评测状态'):
            if row.get(col) and row[col] not in ENUMS[col]:
                fail(f'{col} 非法值：{row[col]}')
        key = tuple(row.get(col, '') for col in (
            ['case_id', 'metric_id', 'run_id', '评审者'] if kind == 'workbench'
            else ['case_id'] if kind == 'dataset' else ['metric_id']))
        if key in seen:
            fail(f'标识重复：{key}')
        seen.add(key)
        if kind == 'dataset':
            mids = metric_ids(row['metric_ids'])
            if not mids or len(mids) != len(set(mids)):
                fail('metric_ids 为空或包含重复编号')
            if metrics and set(mids) - set(metrics):
                fail('包含未声明的 metric_id')
        if kind != 'workbench':
            continue
        if metrics and row['metric_id'] not in metrics:
            fail('包含未声明的 metric_id')
        if initial and (any(row[col] for col in COLUMNS[kind][7:17]) or row['评测状态'] not in ('', '待输出')):
            fail('初始输出、评分、证据、样本问题必须为空，状态仅可空或待输出')
        for side in ('基线', '候选'):
            output, score, gate = (row[side + suffix] for suffix in ('输出', '评分', '硬门槛'))
            if output and not row[side + '版本']:
                fail(f'{side}输出缺少版本标识')
            if (score or gate) and not output:
                fail(f'{side}没有输出却填写评分或硬门槛')
            if gate and gate not in ENUMS['硬门槛']:
                fail(f'{side}硬门槛非法值')
            if score:
                if row['评分方式'] == '二值' and score not in ('通过', '不通过'):
                    fail(f'{side}二值评分只能通过/不通过')
                if row['评分方式'] == '1-5' and score not in ('1', '2', '3', '4', '5'):
                    fail(f'{side}1-5评分必须是1至5的整数')
                if row['评分方式'] == 'GSB':
                    fail('GSB 方法的单版本评分列应为空')
            out_key = (row['case_id'], row['run_id'], row['评审者'], side)
            if output:
                previous = output_by_case.setdefault(out_key, output)
                if previous != output:
                    fail(f'同一运行/样本的{side}输出在不同指标间不一致')
        if row['GSB']:
            if row['GSB'] not in ('G', 'S', 'B') or row['评分方式'] != 'GSB':
                fail('GSB 标签或评分方法错误')
            if not row['基线输出'] or not row['候选输出']:
                fail('GSB 必须有成对输出')
        has_scores = any(row[col] for col in ('基线评分','候选评分','GSB','基线硬门槛','候选硬门槛'))
        if has_scores and (not row['规则编号'] or not row['输出证据']):
            fail('评分必须包含规则编号与输出证据')
        status = row['评测状态']
        issue = row['样本问题']
        if issue and issue != '无' and status != '样本待修订':
            fail('样本存在问题时状态必须为样本待修订')
        if status == '样本待修订' and (issue not in ENUMS['样本问题'][1:] or not row['输出证据']):
            fail('样本待修订需要明确问题类型和证据')
        if status == '不适用':
            if not row['输出证据'] or not row['规则编号'] or issue != '无' or has_scores:
                fail('不适用需规则、原因、样本问题=无，且评分/门槛列留空')
        if status == '已评分':
            if not row['候选输出'] or not row['候选硬门槛'] or issue != '无':
                fail('已评分需要候选输出、门槛状态及样本问题=无')
            if not row['规则编号'] or not row['输出证据']:
                fail('已评分缺少规则或证据')
            if row['评分方式'] == 'GSB' and not row['GSB']:
                fail('已评分缺少 GSB 标签')
            if row['评分方式'] in ('二值','1-5') and not row['候选评分']:
                fail('已评分缺少候选评分')
            if row['基线输出']:
                if not row['基线硬门槛']:
                    fail('基线输出缺少门槛检查')
                if row['评分方式'] in ('二值','1-5') and not row['基线评分']:
                    fail('基线输出缺少评分')
        if status == '待输出' and row['候选输出'] and (row['评分方式'] != 'GSB' or row['基线输出']):
            fail('输出齐备后不应仍标待输出')
    if kind == 'dataset':
        counts = Counter(mid for row in rows for mid in set(metric_ids(row['metric_ids'])))
        if metrics:
            for mid in metrics:
                if counts[mid] < minimum:
                    errors.append(f'{mid} 覆盖 {counts[mid]} 条，少于 {minimum}')
        else:
            warnings.append('未提供 --metrics；未验证目标卡全部指标的覆盖要求')
        inputs = Counter(row['测试输入'] for row in rows)
        if any(value and count > 1 for value, count in inputs.items()):
            errors.append('测试输入完全重复；若环境不同，请把区别纳入测试输入')
        warnings.append('样本比例需与已确认覆盖矩阵人工核对；语义去重和约束冲突不由脚本判定')
    if kind == 'workbench':
        for col in ('run_id', '评审者', '基线版本', '候选版本'):
            if len({row[col] for row in rows if row[col]}) > 1:
                errors.append(f'{col} 包含多个值；默认工作簿必须按运行、评审者、版本分开汇总')
    if kind in ('standard','summary'):
        warnings.append('本模式仅校验字段、必填项、标识与方法；锚点、阈值及公式需人工/表格工具复核')
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', type=Path)
    parser.add_argument('--schema', choices=COLUMNS, default='dataset')
    parser.add_argument('--initial', action='store_true')
    parser.add_argument('--metrics', nargs='+')
    parser.add_argument('--min-coverage', type=int, default=5)
    parser.add_argument('--expected-count', type=int)
    parser.add_argument('--allow-empty', action='store_true', help='仅用于空模板检查')
    args = parser.parse_args()
    if args.min_coverage < 0 or (args.expected_count is not None and args.expected_count < 0):
        parser.error('数量不能为负数')
    try:
        with args.csv_file.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            headers, rows = reader.fieldnames or [], list(reader)
        errors, warnings = validate(headers, rows, args.schema, args.initial, args.metrics,
                                    args.min_coverage, args.expected_count, args.allow_empty)
    except (OSError, UnicodeError, csv.Error) as exc:
        print('ERROR:', exc)
        return 1
    for item in warnings:
        print('WARNING:', item)
    for item in errors:
        print('ERROR:', item)
    print(f'{"FAILED" if errors else "PASSED"}: {len(rows)} rows, {len(errors)} errors')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
