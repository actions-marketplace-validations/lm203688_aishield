# -*- coding: utf-8 -*-
"""
契约测试：`scripts/sync_version.py` 的每个 TARGETS 条目都必须指向仓库内
真实存在的文件。

背景（2026-09-15 真实事故）
---------------------------
给 sync_version 扩面（把公开静态面纳入版本门禁）时，误登记了
`aishield_home.html` —— 它是根目录下一份**未被引用的本地重复副本**，
从未进入仓库。结果：

  * 本地：文件存在  → `--check` 退出 0（本地绿）
  * CI  ：文件不在  → 「❌ 文件不存在」→ 退出 1（CI 红）

这正是本项目「本地绿 ≠ CI 绿」铁律的又一实例：门禁引用了仓库里
不存在的路径。本测试把该不变量钉死：门禁目标 ⊆ 仓库真实文件。
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if os.path.join(ROOT, 'scripts') not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, 'scripts'))

import sync_version  # noqa: E402


class TestSyncVersionTargetsExist(unittest.TestCase):

    def test_targets_nonempty(self):
        self.assertTrue(sync_version.TARGETS,
                        'TARGETS 为空，版本门禁形同虚设')

    def test_every_target_file_exists(self):
        missing = []
        for rel, _pattern, _tmpl in sync_version.TARGETS:
            if not os.path.exists(os.path.join(ROOT, rel)):
                missing.append(rel)
        self.assertEqual(
            missing, [],
            'sync_version.TARGETS 引用了仓库中不存在的文件——'
            '本地可能因残留副本而误绿，CI 会直接判红：%r' % (missing,))

    def test_no_local_only_stray_registered(self):
        """显式点名：这些是本地残留副本，绝不能进版本门禁。"""
        strays = {'aishield_home.html'}
        targets = {rel for rel, _p, _t in sync_version.TARGETS}
        hit = strays & targets
        self.assertEqual(hit, set(),
                         '本地残留副本不应登记进版本门禁：%r' % (hit,))

    def test_patterns_compile_and_are_anchored(self):
        for rel, pattern, _tmpl in sync_version.TARGETS:
            with self.subTest(target=rel):
                rx = re.compile(pattern)
                self.assertIn('(', pattern, '模式必须含捕获组：%s' % rel)

    def test_repo_files_have_expected_version(self):
        """门禁读到的版本必须与基准一致（回归：防再次漂移）。"""
        items = sync_version.read_all()
        base = sync_version.baseline(items)
        vals = {it.get('version') for it in items
                if it.get('version') and it.get('version') != '?'}
        self.assertEqual(vals, {base},
                         '检测到多个版本：%r（基准 %s）' % (sorted(vals), base))


if __name__ == '__main__':
    unittest.main(verbosity=2)
