from __future__ import annotations

from pathlib import Path
import os
import subprocess


def make_hidden_subprocess_kwargs(extra_creationflags: int = 0) -> dict:
\
\
\
       
    kwargs = {}

    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0

        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | extra_creationflags

    return kwargs


class ComsolRunError(RuntimeError):
    pass


class ComsolRunCancelled(RuntimeError):
    pass


class ComsolRunner:
    def __init__(
        self,
        comsolcompile_path: str | Path,
        comsolbatch_path: str | Path,
        work_dir: str | Path | None = None,
    ):
        self.comsolcompile_path = Path(comsolcompile_path)
        self.comsolbatch_path = Path(comsolbatch_path)
        self.work_dir = Path(work_dir) if work_dir is not None else None
        self.current_process: subprocess.Popen | None = None
        self.stop_requested = False

    def stop(self) -> None:
\
\
\
\
           
        self.stop_requested = True

        process = self.current_process
        if process is None or process.poll() is not None:
            return

        if os.name == "nt":
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    **make_hidden_subprocess_kwargs(),
                )
                return
            except Exception:
                pass

        try:
            process.terminate()
        except Exception:
            pass

        try:
            process.wait(timeout=5)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def _raise_if_stopped(self):
        if self.stop_requested:
            raise ComsolRunCancelled("COMSOL 计算已被用户停止。")

    def _creation_flags(self) -> int:
        if os.name == "nt":
            return getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        return 0

    def _run_command(self, cmd: list[str], cwd: Path, failure_title: str) -> tuple[str, str]:
        self._raise_if_stopped()

        process = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            **make_hidden_subprocess_kwargs(self._creation_flags()),
        )

        self.current_process = process

        try:
            stdout, stderr = process.communicate()
            returncode = process.returncode
        finally:
            if self.current_process is process:
                self.current_process = None

        if self.stop_requested:
            raise ComsolRunCancelled("COMSOL 计算已被用户停止。")

        if returncode != 0:
            raise ComsolRunError(
                f"{failure_title}\n\n"
                f"命令：{' '.join(cmd)}\n\n"
                f"STDOUT:\n{stdout}\n\n"
                f"STDERR:\n{stderr}"
            )

        return stdout, stderr

    def compile_java(self, java_path: str | Path) -> Path:
        java_path = Path(java_path).resolve()

        if not java_path.exists():
            raise FileNotFoundError(f"Java 文件不存在：{java_path}")

        if not self.comsolcompile_path.exists():
            raise FileNotFoundError(f"comsolcompile 不存在：{self.comsolcompile_path}")

        cmd = [
            str(self.comsolcompile_path),
            str(java_path),
        ]

        self._run_command(
            cmd=cmd,
            cwd=self.work_dir or java_path.parent,
            failure_title="COMSOL Java 编译失败。",
        )

        class_path = java_path.with_suffix(".class")

        if not class_path.exists():
            raise FileNotFoundError(f"编译结束但未找到 class 文件：{class_path}")

        return class_path

    def run_class(
        self,
        class_path: str | Path,
        *,
        log_path: str | Path | None = None,
        output_mph_path: str | Path | None = None,
    ) -> None:
        class_path = Path(class_path).resolve()

        if not class_path.exists():
            raise FileNotFoundError(f"class 文件不存在：{class_path}")

        if not self.comsolbatch_path.exists():
            raise FileNotFoundError(f"comsolbatch 不存在：{self.comsolbatch_path}")

        cmd = [
            str(self.comsolbatch_path),
            "-inputfile",
            str(class_path),
        ]

        if output_mph_path is not None:
            output_mph_path = Path(output_mph_path).resolve()
            output_mph_path.parent.mkdir(parents=True, exist_ok=True)
            cmd += ["-outputfile", str(output_mph_path)]

        if log_path is not None:
            log_path = Path(log_path).resolve()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            cmd += ["-batchlog", str(log_path)]

        self._run_command(
            cmd=cmd,
            cwd=self.work_dir or class_path.parent,
            failure_title="COMSOL batch 运行失败。",
        )
