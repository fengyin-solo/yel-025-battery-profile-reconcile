"""Acceptance tests for hidden-channel fingerprint reconciliation."""

import copy
import json
import os
import subprocess
import sys

import pytest


ENTRY = os.environ.get("BATTERY_PROFILE_ENTRY", "/app/battery_profile_reconcile.py")
PROFILES = [{'cell_id': 'BATTERY-A', 'fingerprint': [48.0, 21.0, 0.4375]},
 {'cell_id': 'BATTERY-B', 'fingerprint': [62.0, 17.5, 0.28225806451612906]},
 {'cell_id': 'BATTERY-C', 'fingerprint': [55.5, 28.0, 0.5045045045045045]},
 {'cell_id': 'BATTERY-D', 'fingerprint': [70.0, 24.0, 0.34285714285714286]},
 {'cell_id': 'BATTERY-E', 'fingerprint': [51.373, 22.483, 0.481125]},
 {'cell_id': 'BATTERY-F', 'fingerprint': [70.706, 19.976, 0.347774]},
 {'cell_id': 'BATTERY-G', 'fingerprint': [67.194, 33.919, 0.64945]},
 {'cell_id': 'BATTERY-H', 'fingerprint': [89.652, 30.772, 0.490857]},
 {'cell_id': 'BATTERY-I', 'fingerprint': [64.865, 28.415, 0.655625]},
 {'cell_id': 'BATTERY-J', 'fingerprint': [88.118, 24.928, 0.478806]}]
READINGS = [{'slot': 'CH-3',
  'charge_ah': 19.200000000000003,
  'soc_delta': 0.4,
  'voltage_step_v': 0.84,
  'current_a': 40.0,
  'temperature_c': 25.0},
 {'slot': 'CH-10',
  'charge_ah': 24.8,
  'soc_delta': 0.4,
  'voltage_step_v': 0.7,
  'current_a': 40.0,
  'temperature_c': 25.0},
 {'slot': 'CH-6',
  'charge_ah': 22.200000000000003,
  'soc_delta': 0.4,
  'voltage_step_v': 1.12,
  'current_a': 40.0,
  'temperature_c': 25.0},
 {'slot': 'CH-13',
  'charge_ah': 28.0,
  'soc_delta': 0.4,
  'voltage_step_v': 0.96,
  'current_a': 40.0,
  'temperature_c': 25.0},
 {'slot': 'CH-9',
  'charge_ah': 20.5492,
  'soc_delta': 0.4,
  'voltage_step_v': 0.89932,
  'current_a': 40.0,
  'temperature_c': 25.0},
 {'slot': 'CH-5',
  'charge_ah': 28.282400000000003,
  'soc_delta': 0.4,
  'voltage_step_v': 0.79904,
  'current_a': 40.0,
  'temperature_c': 25.0},
 {'slot': 'CH-12',
  'charge_ah': 26.8776,
  'soc_delta': 0.4,
  'voltage_step_v': 1.3567599999999997,
  'current_a': 40.0,
  'temperature_c': 25.0},
 {'slot': 'CH-8',
  'charge_ah': 35.860800000000005,
  'soc_delta': 0.4,
  'voltage_step_v': 1.23088,
  'current_a': 40.0,
  'temperature_c': 25.0},
 {'slot': 'CH-4',
  'charge_ah': 25.945999999999998,
  'soc_delta': 0.4,
  'voltage_step_v': 1.1365999999999998,
  'current_a': 40.0,
  'temperature_c': 25.0},
 {'slot': 'CH-11',
  'charge_ah': 35.2472,
  'soc_delta': 0.4,
  'voltage_step_v': 0.99712,
  'current_a': 40.0,
  'temperature_c': 25.0}]
EXPECTED_ROWS = [{'slot': 'CH-10', 'cell_id': 'BATTERY-B', 'residual': 5.227014117056199e-26},
 {'slot': 'CH-11', 'cell_id': 'BATTERY-D', 'residual': 0.02267232644730319},
 {'slot': 'CH-12', 'cell_id': 'BATTERY-G', 'residual': 0.015706901769415187},
 {'slot': 'CH-13', 'cell_id': 'BATTERY-J', 'residual': 0.04086511816938981},
 {'slot': 'CH-3', 'cell_id': 'BATTERY-A', 'residual': 0.0},
 {'slot': 'CH-4', 'cell_id': 'BATTERY-C', 'residual': 0.011076454129783803},
 {'slot': 'CH-5', 'cell_id': 'BATTERY-F', 'residual': 0.010717627619348673},
 {'slot': 'CH-6', 'cell_id': 'BATTERY-I', 'residual': 0.02307585583387205},
 {'slot': 'CH-8', 'cell_id': 'BATTERY-H', 'residual': 0.03132213884013917},
 {'slot': 'CH-9', 'cell_id': 'BATTERY-E', 'residual': 0.002239861075781767}]
OUTPUT_KEYS = ['pack_id', 'status', 'cell_assignments', 'total_residual', 'accepted', 'diagnostic']
LEDGER_KEYS = ['pack_id', 'input_sha256', 'result_sha256', 'total_residual']


def base_payload():
    return {
        "pack_id": "BATTERY-STD-7",
        "limits": {"max_slots": 12, "residual_ceiling": 0.02},
        "profiles": copy.deepcopy(PROFILES),
        "readings": copy.deepcopy(READINGS),
    }


def invoke(tmp_path, payload=None, ledger=None, raw=None, output_name="result.json"):
    source = tmp_path / "readings.json"
    target = tmp_path / output_name
    if raw is None:
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    source.write_bytes(raw.encode("utf-8"))
    command = [sys.executable, ENTRY, str(source), str(target)]
    if ledger is not None:
        command.append(str(ledger))
    completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
    return completed, source, target


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_success_writes_aligned_output_quietly(tmp_path):
    """题面：「成功时 stdout 和 stderr 都必须为空，结果文件是唯一成功信号。」"""
    result, _, output = invoke(tmp_path, base_payload())
    assert result.returncode == 0
    assert result.stdout == "" and result.stderr == ""
    assert output.is_file()


def test_global_assignment_is_minimum_residual(tmp_path):
    """题面：「电池槽位必须采用总指纹误差最小的全局对应，而不是按读入顺序配对。」"""
    result, _, output = invoke(tmp_path, base_payload())
    document = read(output)
    assert result.returncode == 0
    assert [(row["slot"], row["cell_id"]) for row in document["cell_assignments"]] == [(row["slot"], row["cell_id"]) for row in EXPECTED_ROWS]
    assert [row["residual"] for row in document["cell_assignments"]] == pytest.approx([row["residual"] for row in EXPECTED_ROWS], abs=1e-12)


def test_assignment_rows_have_exact_fields(tmp_path):
    """题面：「每条cell_assignments记录恰好包含 slot、cell_id 和 residual 三个键。」"""
    result, _, output = invoke(tmp_path, base_payload())
    document = read(output)
    assert result.returncode == 0
    assert all(set(row) == {"slot", "cell_id", "residual"} for row in document["cell_assignments"])


def test_output_has_exact_top_level_keys(tmp_path):
    """题面：「结果根对象恰好包含 pack_id、status、cell_assignments、total_residual、accepted 和 diagnostic 六个键。」"""
    result, _, output = invoke(tmp_path, base_payload())
    document = read(output)
    assert result.returncode == 0
    assert list(document) == OUTPUT_KEYS


def test_output_is_compact_utf8_with_single_lf(tmp_path):
    """题面：「结果文件使用紧凑 UTF-8 JSON，末尾只有一个 LF。」"""
    result, _, output = invoke(tmp_path, base_payload())
    raw = output.read_bytes()
    assert result.returncode == 0
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    assert b": " not in raw and b", " not in raw


def test_total_residual_matches_assignment(tmp_path):
    """题面：「total_residual 是最终对应中所有 residual 之和。」"""
    result, _, output = invoke(tmp_path, base_payload())
    document = read(output)
    total = sum(row["residual"] for row in document["cell_assignments"])
    assert result.returncode == 0
    assert document["total_residual"] == pytest.approx(total, abs=1e-12)
    assert document["total_residual"] == pytest.approx(0.15767628388503369, abs=1e-10)


def test_ceiling_accepts_inside_case(tmp_path):
    """题面：「总误差不超过 residual_ceiling 时 accepted 为 true。」"""
    payload = base_payload()
    payload["limits"]["residual_ceiling"] = 1.0
    payload["profiles"][0]["fingerprint"] = [value * 1.04 for value in payload["profiles"][0]["fingerprint"]]
    result, _, output = invoke(tmp_path, payload)
    document = read(output)
    assert result.returncode == 0 and document["accepted"] is True
    assert document["status"] == "matched"


def test_ceiling_quarantines_first_outside_value(tmp_path):
    """题面：「总误差超过 residual_ceiling 时仍保留结果，但 accepted 为 false 且 status 为 quarantined。」"""
    payload = base_payload()
    payload["limits"]["residual_ceiling"] = 0.0001
    payload["profiles"][0]["fingerprint"] = [value * 1.04 for value in payload["profiles"][0]["fingerprint"]]
    result, _, output = invoke(tmp_path, payload)
    document = read(output)
    assert result.returncode == 0 and document["accepted"] is False
    assert document["status"] == "quarantined"


def test_missing_top_level_key_is_refused(tmp_path):
    """题面：「顶层缺键时以 1 结束并输出 分档拒收: BAD_PROFILE。」"""
    payload = base_payload()
    payload.pop("limits")
    result, _, output = invoke(tmp_path, payload)
    assert result.returncode == 1 and result.stderr == "分档拒收: BAD_PROFILE\n" and not output.exists()


def test_extra_top_level_key_is_refused(tmp_path):
    """题面：「顶层多键时以 1 结束并输出 分档拒收: BAD_PROFILE。」"""
    payload = base_payload()
    payload["memo"] = "shift"
    result, _, output = invoke(tmp_path, payload)
    assert result.returncode == 1 and result.stderr == "分档拒收: BAD_PROFILE\n" and not output.exists()


def test_duplicate_top_level_key_is_refused(tmp_path):
    """题面：「同一对象出现重复键时按输入损坏处理并输出 分档拒收: BAD_PROFILE。」"""
    payload = base_payload()
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    raw = raw.replace('"pack_id":"', '"pack_id":"duplicate", "pack_id":"', 1) + "\n"
    result, _, output = invoke(tmp_path, raw=raw)
    assert result.returncode == 1 and result.stderr == "分档拒收: BAD_PROFILE\n" and not output.exists()


def test_boolean_numeric_is_refused(tmp_path):
    """题面：「数值字段使用布尔值时不得当作有限数并输出 分档拒收: BAD_PROFILE。」"""
    payload = base_payload()
    payload["readings"][0]["charge_ah"] = True
    result, _, output = invoke(tmp_path, payload)
    assert result.returncode == 1 and result.stderr == "分档拒收: BAD_PROFILE\n" and not output.exists()


def test_profile_fingerprint_length_is_refused(tmp_path):
    """题面：「每个指纹必须恰好有三个正有限分量，否则输出 分档拒收: BAD_PROFILE。」"""
    payload = base_payload()
    payload["profiles"][0]["fingerprint"].pop()
    result, _, output = invoke(tmp_path, payload)
    assert result.returncode == 1 and result.stderr == "分档拒收: BAD_PROFILE\n" and not output.exists()


def test_duplicate_slot_is_refused(tmp_path):
    """题面：「`pack_id` 使用 2 至 40 个可打印字符，首尾不得有空白，也不接收控制字符。」"""
    payload = base_payload()
    payload["readings"][1]["slot"] = payload["readings"][0]["slot"]
    result, _, output = invoke(tmp_path, payload)
    assert result.returncode == 1 and result.stderr == "分档拒收: BAD_PROFILE\n" and not output.exists()
    minimum = base_payload()
    minimum["pack_id"] = "AB"
    minimum_result, _, minimum_output = invoke(tmp_path, minimum, output_name="minimum.json")
    assert minimum_result.returncode == 0 and read(minimum_output)["pack_id"] == "AB"
    maximum = base_payload()
    maximum["pack_id"] = "P" * 40
    maximum_result, _, maximum_output = invoke(tmp_path, maximum, output_name="maximum.json")
    assert maximum_result.returncode == 0 and read(maximum_output)["pack_id"] == "P" * 40
    internal_space = base_payload()
    internal_space["pack_id"] = "A B"
    space_result, _, space_output = invoke(tmp_path, internal_space, output_name="space.json")
    assert space_result.returncode == 0 and read(space_output)["pack_id"] == "A B"
    tabbed = base_payload()
    tabbed["pack_id"] = "A\tB"
    tab_result, _, tab_output = invoke(tmp_path, tabbed, output_name="tab.json")
    assert tab_result.returncode == 1 and tab_result.stderr == "分档拒收: BAD_PROFILE\n" and not tab_output.exists()


def test_ledger_has_exact_shape_and_is_idempotent(tmp_path):
    """题面：「完全相同的输入和结果再次运行时，留痕簿字节保持不变。」"""
    ledger = tmp_path / "trail.jsonl"
    result, _, output = invoke(tmp_path, payload=base_payload(), ledger=ledger)
    first = ledger.read_bytes()
    second, _, _ = invoke(tmp_path, payload=base_payload(), ledger=ledger)
    item = json.loads(first)
    assert result.returncode == 0 and second.returncode == 0
    assert list(item) == LEDGER_KEYS and first.endswith(b"\n")
    assert ledger.read_bytes() == first and second.stdout == "" and second.stderr == ""


def test_different_result_appends_one_ledger_line(tmp_path):
    """题面：「不同结果成功产生后，留痕簿按成功顺序追加一行。」"""
    ledger = tmp_path / "trail.jsonl"
    first, _, _ = invoke(tmp_path, payload=base_payload(), ledger=ledger)
    changed = base_payload()
    changed["pack_id"] = "BATTERY-STD-8"
    second, _, _ = invoke(tmp_path, payload=changed, ledger=ledger)
    assert first.returncode == 0 and second.returncode == 0
    assert len(ledger.read_bytes().splitlines()) == 2
    assert ledger.read_bytes().endswith(b"\n")


def test_ledger_path_equal_to_output_is_refused(tmp_path):
    """题面：「留痕簿路径与结果路径相同时输出 流水拒收: BAD_BATTERY_LEDGER。」"""
    payload = base_payload()
    source = tmp_path / "readings.json"
    target = tmp_path / "same.json"
    source.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    result = subprocess.run([sys.executable, ENTRY, str(source), str(target), str(target)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 1 and result.stderr == "流水拒收: BAD_BATTERY_LEDGER\n" and not target.exists()


def test_io_failure_preserves_existing_target(tmp_path):
    """题面：「结果目标不可写时输出 写出失败: BATTERY_IO，既有结果保持原样。」"""
    target = tmp_path / "occupied"
    target.mkdir()
    source = tmp_path / "readings.json"
    source.write_text(json.dumps(base_payload(), separators=(",", ":")), encoding="utf-8")
    result = subprocess.run([sys.executable, ENTRY, str(source), str(target)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 1 and result.stderr == "写出失败: BATTERY_IO\n"
    assert target.exists() and target.is_dir() and not any(target.iterdir()) and "traceback" not in result.stderr.lower()


def test_wrong_argument_count_is_refused(tmp_path):
    """题面：「命令行没有按声明给出输入与结果路径时，以 1 结束并输出 分档拒收: BAD_PROFILE。」"""
    target = tmp_path / "result.json"
    result = subprocess.run([sys.executable, ENTRY], capture_output=True, text=True, timeout=30)
    assert result.returncode == 1 and result.stderr == "分档拒收: BAD_PROFILE\n" and not target.exists()
