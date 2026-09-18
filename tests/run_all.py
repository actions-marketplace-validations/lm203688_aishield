"""
运行所有测试 — 串联 test_linkages, test_geo, test_security, test_hupijiao,
test_governance, test_mcp_contract 等

用法:
  python tests/run_all.py
  python tests/run_all.py -v          # 详细模式
  python -m tests.run_all            # 模块方式运行
"""

import unittest
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 加载所有测试文件
    test_files = [
        'tests.test_linkages',
        'tests.test_geo',
        'tests.test_security',
        'tests.test_supply_chain',
        'tests.test_client_discovery',
        'tests.test_ci_contract',
        'tests.test_commercialization',
        'tests.test_hupijiao',
        'tests.test_governance',
        'tests.test_mcp_contract',
        'tests.test_tech_radar',
        'tests.test_workspace_scan',
        'tests.test_sandbox_rules',
        'tests.test_guardrail_harness',
        'tests.test_attestation_live',
        'tests.test_distribution_gate',
        'tests.test_trust_api',
        'tests.test_identity_network_scan',
        'tests.test_capability_boundary_scan',
        'tests.test_capability_full_scan',
        'tests.test_agent_security_gateway',
        'tests.test_trust_protocol',
        'tests.test_claim_lock',
        'tests.test_replay',
        'tests.test_vertical_risk',
        'tests.test_diff',
        'tests.test_fuzzing',
        'tests.test_baseline_scan',
        'tests.test_compliance',
        'tests.test_fleet_versions',
        'tests.test_runtime_behavior',
        'tests.test_self_reference',
        'tests.test_vuln_feed_health',
        'tests.test_radar_effect',
        'tests.test_digest_window',
        'tests.test_stale_exemptions',
        'tests.test_finding_anchor',
        'tests.test_isolation_invariants',
        'tests.test_sync_version_targets',
        'tests.test_no_hardcoded_cf_token',
        # 2026-09-16 补登记：下列文件此前不在列表中，被 run_all 静默跳过。
        # 本清单是硬编码的，新增测试文件若忘记登记就不会被执行（假绿），
        # tests/test_ci_contract.py::TestRunnerCoverage 会把这件事钉死。
        # 注意：tests.test_geo 已在上方登记，此处不得重复 —— 重复会让整个模块跑两遍，
        # 既拖慢 CI，又让单个失败在日志里重复出现两次、误判为两个缺陷
        # （2026-09-17 root 护栏那条 CI 全红就是被这个假象掩盖了）。
        'tests.test_indexnow',
        'tests.test_gap_fill',
        'tests.test_rule_promotion_rollback',
        # 2026-09-17 新增扫描器（ASI04 记忆完整性）的回归测试
        'tests.test_memory_integrity_scan',
        'tests.test_promote_rule_shadow',  # shadow/enforce 双模式 + 雷达加载期字段契约
        'tests.test_deployment_root_guard',  # 2026-09-18：root 护栏与部署身份冲突 = 20.5h 静默 502
        'tests.test_deployment_observability',  # 退出码传导契约：诊断语句不得抢占部署/自愈的退出码
        'tests.test_notify_hardening',  # 2026-09-18：告警链路出站脱敏 + fail-closed 退出码 + 未送达台账闭环
        'tests.test_rule_audit_contract',  # 2026-09-18：基线审计契约（零 critical 误报/引用抑制/情报去重/对抗式评审闸门有效）
    ]

    loaded = 0
    for tf in test_files:
        try:
            suite.addTests(loader.loadTestsFromName(tf))
            loaded += 1
        except Exception as e:
            print(f"  [SKIP] {tf}: {e}")

    print(f"\n{'=' * 60}")
    print(f"AIShield Test Suite")
    print(f"Loaded {loaded}/{len(test_files)} test modules")
    print(f"{'=' * 60}\n")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出摘要
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\n{'=' * 60}")
    print(f"AIShield Test Suite Summary")
    print(f"{'=' * 60}")
    print(f"Total:    {result.testsRun}")
    print(f"Passed:   {passed}")
    print(f"Failed:   {len(result.failures)}")
    print(f"Errors:   {len(result.errors)}")
    print(f"Skipped:  {len(result.skipped)}")
    print(f"{'=' * 60}")

    if result.wasSuccessful():
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        if result.failures:
            print(f"\n--- Failures ({len(result.failures)}) ---")
            for test, traceback in result.failures:
                print(f"  FAIL: {test}")
        if result.errors:
            print(f"\n--- Errors ({len(result.errors)}) ---")
            for test, traceback in result.errors:
                print(f"  ERROR: {test}")

    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
