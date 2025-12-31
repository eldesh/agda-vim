from __future__ import annotations
import subprocess
import logging
from typing import IO

from .agda_version import AgdaVersion

logger = logging.getLogger(__name__)

class AgdaProcess:
    """Agda process wrapper class for managing an Agda subprocess.

    Attributes:
        _process (subprocess.Popen): The subprocess running the Agda process.
        _path (str): The file path to the Agda executable.
        _version (AgdaVersion): The version of the Agda process.
    """
    _process: subprocess.Popen[str]
    _path: str
    _version: AgdaVersion

    def __init__(self, path: str):
        self._path = path
        self._process = subprocess.Popen(
            [self._path, "--interaction"],
            bufsize = 1,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            universal_newlines = True
        )
        self._version = AgdaVersion.parse(subprocess.run(
            [self._path, '--version'],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip())

    @property
    def path(self) -> str:
        return self._path

    @property
    def version(self) -> AgdaVersion:
        return self._version

    @property
    def stdin(self) -> IO[str]:
        assert self._process.stdin is not None
        return self._process.stdin

    @property
    def stdout(self) -> IO[str]:
        assert self._process.stdout is not None
        return self._process.stdout

    def restart(self, path: str):
        '''Terminates the current Agda process and starts a new one located at `path`.'''
        self.stop_wait()
        AgdaProcess.__init__(self, path)

    def stop_wait(self):
        '''Terminates the current Agda process and waits for it to exit. If it does not exit within 10 seconds, it is killed.'''
        try:
            self._process.terminate()
            self._process.wait(timeout = 10)
        except subprocess.TimeoutExpired:
            logger.error("Agda process did not exit in time, killing it.")
            self._process.kill()
            self._process.wait()
