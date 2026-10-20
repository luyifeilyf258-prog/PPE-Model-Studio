from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import subprocess
from typing import Mapping


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


@dataclass(frozen=True)
class ComsolBatchResult:
    output_mph_path: Path | None
    requested_mph_path: Path | None
    log_path: Path | None


class ComsolRunError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        returncode: int | None = None,
        output_mph_path: Path | None = None,
        log_path: Path | None = None,
        error_summary: str | None = None,
    ):
        super().__init__(message)
        self.returncode = returncode
        self.output_mph_path = output_mph_path
        self.log_path = log_path
        self.error_summary = error_summary


class ComsolRunCancelled(RuntimeError):
    pass


_COMSOL_ERROR_MARKERS = (
    "/*****错误",
    "运行 Java 类时出错",
    "NaN/Inf",
    "Error running Java class",
    "Undefined value found",
    "Failed to find a solution",
)


def read_comsol_log(log_path: str | Path | None) -> str:
    if log_path is None:
        return ""
    path = Path(log_path)
    if not path.exists():
        return ""
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def extract_comsol_error_summary(log_text: str, max_lines: int = 16) -> str | None:
    lines = log_text.splitlines()
    first_error_index = None
    for index, line in enumerate(lines):
        if any(marker.casefold() in line.casefold() for marker in _COMSOL_ERROR_MARKERS):
            first_error_index = index
            break
    if first_error_index is None:
        return None
    useful = [line.strip() for line in lines[first_error_index:] if line.strip()]
    return "\n".join(useful[:max_lines])


def extract_comsol_version(log_text: str) -> str | None:
    match = re.search(r"COMSOL Multiphysics\s+([0-9]+(?:\.[0-9]+)+)", log_text)
    return match.group(1) if match else None


def csv_has_data(csv_path: str | Path) -> bool:
    path = Path(csv_path)
    if not path.is_file() or path.stat().st_size == 0:
        return False
    content_lines = [
        line for line in read_comsol_log(path).splitlines()
        if line.strip() and not line.lstrip().startswith("%")
    ]
    return len(content_lines) >= 2


def _snapshot_mph_files(directory: Path) -> dict[Path, tuple[int, int]]:
    if not directory.exists():
        return {}
    return {
        path.resolve(): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in directory.glob("*.mph") if path.is_file()
    }


def _find_fresh_mph_file(
    requested_path: Path,
    before: Mapping[Path, tuple[int, int]],
) -> Path | None:
    directory = requested_path.parent
    candidates = []
    if requested_path.is_file():
        candidates.append(requested_path.resolve())
    candidates.extend(path.resolve() for path in directory.glob(f"{requested_path.stem}_*.mph"))
    candidates.extend(path.resolve() for path in directory.glob("*.mph"))
    fresh = []
    for path in dict.fromkeys(candidates):
        if not path.is_file():
            continue
        current = (path.stat().st_mtime_ns, path.stat().st_size)
        if before.get(path) != current:
            fresh.append(path)
    return max(fresh, key=lambda path: path.stat().st_mtime_ns) if fresh else None


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
                f"STDERR:\n{stderr}",
                returncode=returncode,
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
    ) -> ComsolBatchResult:
        class_path = Path(class_path).resolve()

        if not class_path.exists():
            raise FileNotFoundError(f"class 文件不存在：{class_path}")

        if not self.comsolbatch_path.exists():
            raise FileNotFoundError(f"comsolbatch 不存在：{self.comsolbatch_path}")

        requested_mph = Path(output_mph_path).resolve() if output_mph_path is not None else None
        resolved_log = Path(log_path).resolve() if log_path is not None else None
        before = _snapshot_mph_files(requested_mph.parent) if requested_mph else {}

        cmd = [str(self.comsolbatch_path), "-inputfile", str(class_path)]

        if requested_mph is not None:
            requested_mph.parent.mkdir(parents=True, exist_ok=True)
            cmd += ["-outputfile", str(requested_mph)]

        if resolved_log is not None:
            resolved_log.parent.mkdir(parents=True, exist_ok=True)
            cmd += ["-batchlog", str(resolved_log)]

        command_error = None
        try:
            self._run_command(
                cmd=cmd,
                cwd=self.work_dir or class_path.parent,
                failure_title="COMSOL batch 运行失败。",
            )
        except ComsolRunError as exc:
            command_error = exc

        actual_mph = _find_fresh_mph_file(requested_mph, before) if requested_mph else None
        error_summary = extract_comsol_error_summary(read_comsol_log(resolved_log))

        if command_error is not None or error_summary is not None:
            details = ["COMSOL batch 求解失败。"]
            if actual_mph is not None:
                details.append(f"模型已保存，可用于诊断或重算：{actual_mph}")
            if error_summary:
                details.append(f"日志错误摘要：\n{error_summary}")
            elif command_error is not None:
                details.append(str(command_error))
            raise ComsolRunError(
                "\n\n".join(details),
                returncode=command_error.returncode if command_error else 0,
                output_mph_path=actual_mph,
                log_path=resolved_log,
                error_summary=error_summary,
            )

        if requested_mph is not None and actual_mph is None:
            raise ComsolRunError(
                "COMSOL batch 已结束，但没有找到本次生成的 MPH 文件。",
                log_path=resolved_log,
            )

        # COMSOL may append the model tag to -outputfile. Normalize successful
        # output so the GUI path and the filesystem agree.
        if requested_mph is not None and actual_mph != requested_mph:
            try:
                actual_mph.replace(requested_mph)
                actual_mph = requested_mph
            except OSError:
                pass

        return ComsolBatchResult(
            output_mph_path=actual_mph,
            requested_mph_path=requested_mph,
            log_path=resolved_log,
        )
