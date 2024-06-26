import os
import pathlib
import subprocess
from typing import Literal, Union

from ccf_parser.status import Status
from utils import judge_logger


class SimpleRuntime(object):
    def __init__(self) -> None:
        pass

    def calling_precheck(self, executeable_file: pathlib.Path, input_content: str, input_type: Literal['STDIN', 'FILE'], file_input_path: pathlib.Path = None, timeout: float = 1.0) -> bool:
        if file_input_path is not None:
            if file_input_path.is_absolute():
                judge_logger.warning(
                    f'执行评测时的输入文件路径 {file_input_path} 是绝对路径，正确的格式应当为 `Path("hello.in")` 一类。\n运行失败，返回状态码 RE。')
                return False

        executeable_file.chmod(0o700)

    def __call__(self, executeable_file: pathlib.Path, input_content: str, input_type: Literal['STDIN', 'FILE'], file_input_path: pathlib.Path = None, timeout: float = 1.0) -> Union[str, Status]:
        """返回 STDOUT（STDOUT 无输出时返回第一个后缀为 .out 的文件的内容）"""
        if self.calling_precheck(executeable_file, input_content, input_type, file_input_path, timeout) is False:
            return Status.RuntimeError

        if input_type == 'STDIN':
            process = self.stdin_executor(executeable_file)
            try:
                stdout, stderr = process.communicate(
                    input_content.encode('utf-8'), timeout=timeout)

                if process.returncode != 0:
                    return Status.RuntimeError

                return stdout.decode('utf-8')
            except subprocess.TimeoutExpired:
                return Status.TimeLimitExceeded
        else:
            process = self.file_input_executor(
                executeable_file, file_input_path, input_content)

            try:
                process.wait(timeout)

                if process.returncode != 0:
                    return Status.RuntimeError

                try:
                    return executeable_file.with_name(file_input_path.name).with_suffix('.out').read_text(encoding='utf-8')
                except:
                    return Status.WrongAnswer
            except subprocess.TimeoutExpired:
                return Status.TimeLimitExceeded

    def file_input_executor(self, executeable_file: pathlib.Path, file_input_path: pathlib.Path, input_content: str) -> subprocess.Popen[bytes]:
        executeable_file.parent.joinpath(file_input_path).write_text(
            input_content, encoding='utf-8')

        process = subprocess.Popen(
            executeable_file.absolute().__str__(),
            bufsize=-1,
            cwd=executeable_file.parent
        )

        return process

    def stdin_executor(self, executeable_file: pathlib.Path) -> subprocess.Popen[bytes]:
        process = subprocess.Popen(
            executeable_file.absolute().__str__(),
            bufsize=-1,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=executeable_file.parent
        )

        return process


# TODO: 暂缓开发安全运行时
# class SafetyRuntimeWithLrun(SimpleRuntime):
#     def __init__(self) -> None:
#         super().__init__()

#         if os.getuid() != 0 or os.getgid() != 0:  # pragma: no cover
#             raise RuntimeError('必须为 Root 用户才能使用 SafetyRuntimeWithLrun。')

#     def __call__(self, executeable_file: pathlib.Path, input_content: str, input_type: Literal['STDIN'] | Literal['FILE'], file_input_path: pathlib.Path = None, timeout: float = 1) -> str | Status:
#         if self.calling_precheck(executeable_file, input_content, input_type, file_input_path, timeout) is False:
#             return Status.RuntimeError

#         if input_type == 'STDIN':
#             self.stdin_executor(executeable_file, network=False, timeout=timeout, max_memory=0, uid=0, gid=0)

#     def stdin_executor(self, executeable_file: pathlib.Path, network: bool, timeout: float, max_memory: int, uid: int, gid: int) -> subprocess.Popen[bytes]:
#         # 注：max_memory 的单位为byte

#         process = subprocess.Popen(
#             [
#                 'sudo',
#                 'lrun',
#                 '--network', 'true' if network else 'false',
#                 '--max-cpu-time', str(timeout),
#                 '--max-memory', str(max_memory),
#                 '--isolate-process', 'true',
#                 '--uid', str(uid),
#                 '--gid', str(gid)
#             ]
#         )

#         return process


simple_runtime = SimpleRuntime()
