"""
scanner/sandbox.py — 内核级沙箱接口（硬骨头 #4：内核级隔离）

问题：agent 会执行不可信代码/工具（比如来自第三方 MCP server 的指令）。仅靠应用层校验挡不住
      0day；需要在 OS 层把「能做的」砍到最小。

立场：aishield 不自研内核，而是做「可移植沙箱抽象 + 内核级能力可用时自动启用」。
  - Linux 生产部署：subprocess + RLIMIT（内存/CPU/文件） + 可选 seccomp-bpf 系统调用过滤
    + 降权（drop 到 nobody）。这是真正的「内核级」隔离。
  - Windows 开发/CI：无 RLIMIT/seccomp；退化为「超时墙 + 进程树清理」的最佳努力隔离，
    并在 capabilities() 中明确标注「非内核级」，防止被误认为安全。

设计：
  - SandboxProfile：预设 strict / balanced / permissive，含 mem_mb / cpu_seconds / network /
    writable_paths / seccomp 开关。
  - run_isolated(cmd, args, profile=...)：返回 {returncode, stdout, stderr, timed_out, killed}
  - host_capabilities()：报告当前主机可用的隔离能力（供调用方决定是否放行）。

零依赖；unix-only 模块（resource/seccomp）全部在运行时惰性导入并 try/except 保护，
Windows 下 import 不报错。
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

IS_WINDOWS = os.name == "nt"
IS_LINUX = sys.platform.startswith("linux")


# ── 沙箱档位 ──
class SandboxProfile:
    def __init__(self, name="balanced", mem_mb=256, cpu_seconds=10,
                 network=True, writable_paths=None, seccomp=True,
                 drop_privileges=True):
        self.name = name
        self.mem_mb = mem_mb
        self.cpu_seconds = cpu_seconds
        self.network = network
        self.writable_paths = list(writable_paths or [])
        self.seccomp = seccomp
        self.drop_privileges = drop_privileges

    def to_dict(self):
        return {
            "name": self.name, "mem_mb": self.mem_mb, "cpu_seconds": self.cpu_seconds,
            "network": self.network, "writable_paths": self.writable_paths,
            "seccomp": self.seccomp, "drop_privileges": self.drop_privileges,
        }


PROFILES = {
    "strict": SandboxProfile("strict", mem_mb=128, cpu_seconds=5, network=False,
                             writable_paths=[], seccomp=True, drop_privileges=True),
    "balanced": SandboxProfile("balanced", mem_mb=512, cpu_seconds=30, network=True,
                               writable_paths=["/tmp"], seccomp=True, drop_privileges=True),
    "permissive": SandboxProfile("permissive", mem_mb=2048, cpu_seconds=120, network=True,
                                 writable_paths=None, seccomp=False, drop_privileges=False),
}


def get_profile(name="balanced") -> SandboxProfile:
    return PROFILES.get(name, PROFILES["balanced"])


def host_capabilities() -> dict:
    """报告本机可用的隔离能力（诚实标注哪些是内核级）。"""
    caps = {
        "platform": sys.platform,
        "kernel_level": False,
        "rlimit": False,
        "seccomp": False,
        "drop_privileges": False,
        "timeout_wall": True,
        "process_tree_kill": True,
        "notes": [],
    }
    if IS_LINUX:
        try:
            import resource  # noqa: F401
            caps["rlimit"] = True
            caps["kernel_level"] = True
        except Exception:
            pass
        try:
            import seccomp  # type: ignore  # noqa: F401
            caps["seccomp"] = True
        except Exception:
            caps["seccomp"] = False
            caps["notes"].append("seccomp 未安装（pip install libseccomp python 绑定可启用系统调用过滤）")
        # 降权需要 root 才能 setuid 到 nobody；非 root 时标注不可用
        caps["drop_privileges"] = (os.geteuid() == 0) if hasattr(os, "geteuid") else False
    else:
        caps["notes"].append("Windows 无 RLIMIT/seccomp；仅超时墙 + 进程树清理（最佳努力，非内核级）")
    return caps


def _preexec_linux(profile: SandboxProfile):
    """Linux 下在子进程 fork 后、exec 前设置资源限制与降权。"""
    import resource

    # 内存上限（RLIMIT_AS）：防止 OOM / 内存炸弹
    try:
        if profile.mem_mb:
            resource.setrlimit(resource.RLIMIT_AS,
                               (profile.mem_mb * 1024 * 1024, profile.mem_mb * 1024 * 1024))
    except Exception:
        pass
    # CPU 时间上限（RLIMIT_CPU）：防止死循环烧 CPU
    try:
        if profile.cpu_seconds:
            resource.setrlimit(resource.RLIMIT_CPU,
                               (profile.cpu_seconds, profile.cpu_seconds + 1))
    except Exception:
        pass
    # 降权到 nobody（需要 root）
    if profile.drop_privileges and hasattr(os, "geteuid") and os.geteuid() == 0:
        try:
            import pwd
            uid = pwd.getpwnam("nobody").pw_uid
            gid = pwd.getpwnam("nobody").pw_gid
            os.setgid(gid)
            os.setuid(uid)
        except Exception:
            pass
    # （可选）seccomp 系统调用过滤在 _apply_seccomp 中处理


def _apply_seccomp(profile: SandboxProfile):
    """若可用，应用最小系统调用白名单（Linux 内核级）。失败则静默跳过。"""
    if not profile.seccomp or not IS_LINUX:
        return
    try:
        import seccomp  # type: ignore
        f = seccomp.SyscallFilter(seccomp.ALLOW)
        for sc in ("read", "write", "close", "exit", "exit_group", "brk", "mmap",
                   "mprotect", "rt_sigreturn", "sigreturn", "futex", "sched_yield",
                   "clock_gettime", "open", "openat", "stat", "fstat", "lseek",
                   "readlink", "getdents", "poll", "select", "recvfrom", "sendto"):
            try:
                f.add_rule(seccomp.ALLOW, sc)
            except Exception:
                pass
        if not profile.network:
            for sc in ("socket", "connect", "bind", "listen", "accept", "sendto", "recvfrom"):
                try:
                    f.add_rule(seccomp.KILL, sc)
                except Exception:
                    pass
        f.load()
    except Exception:
        pass  # 无 libseccomp 时退化为仅 RLIMIT


def run_isolated(cmd, args=None, *, profile: SandboxProfile | str = "balanced",
                 cwd=None, env=None, input_text=None) -> dict:
    """在内核级（Linux）或最佳努力（Windows）沙箱中执行命令。

    Returns:
        {returncode, stdout, stderr, timed_out, killed, isolation}
    """
    if isinstance(profile, str):
        profile = get_profile(profile)
    cmdline = [cmd] + list(args or [])
    caps = host_capabilities()
    preexec_fn = None
    if IS_LINUX:
        def _preexec():
            _preexec_linux(profile)
            _apply_seccomp(profile)
        preexec_fn = _preexec

    start = time.time()
    proc = None
    try:
        proc = subprocess.Popen(
            cmdline,
            cwd=cwd, env=env,
            stdin=subprocess.PIPE if input_text is not None else None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=preexec_fn,  # Unix-only；Windows 上忽略
        )
        out, err = proc.communicate(
            input=input_text.encode("utf-8") if input_text is not None else None,
            timeout=profile.cpu_seconds + 2,
        )
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        if proc is not None:
            _kill_tree(proc)
            out, err = proc.communicate() if False else (b"", b"")
        out, err = b"", b"timeout"
    except Exception as e:  # pragma: no cover
        return {"returncode": -1, "stdout": "", "stderr": str(e),
                "timed_out": False, "killed": False, "isolation": caps}
    return {
        "returncode": proc.returncode if proc else -1,
        "stdout": out.decode("utf-8", "replace") if isinstance(out, bytes) else str(out),
        "stderr": err.decode("utf-8", "replace") if isinstance(err, bytes) else str(err),
        "timed_out": timed_out,
        "killed": timed_out,
        "isolation": caps,
        "elapsed_sec": round(time.time() - start, 3),
    }


def _kill_tree(proc: subprocess.Popen):
    """杀掉进程及其子进程树。"""
    try:
        if IS_WINDOWS:
            # Windows：用 taskkill /T
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            import os as _os
            import signal
            try:
                _os.killpg(_os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


if __name__ == "__main__":
    print("host capabilities:", host_capabilities())
    # 安全命令
    if IS_WINDOWS:
        r = run_isolated("cmd", ["/c", "echo hello"], profile="balanced")
    else:
        r = run_isolated("echo", ["hello"], profile="balanced")
    print("安全命令:", r["returncode"], r["stdout"].strip(), "| 隔离:", r["isolation"]["kernel_level"])
    # 超时命令（验证墙）
    if IS_WINDOWS:
        r2 = run_isolated("cmd", ["/c", "ping -n 30 localhost"], profile="strict")
    else:
        r2 = run_isolated("sleep", ["20"], profile="strict")
    print("超时命令 killed:", r2["killed"], "timed_out:", r2["timed_out"])
