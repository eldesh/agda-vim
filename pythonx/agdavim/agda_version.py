from __future__ import annotations
from dataclasses import dataclass

@dataclass(order=True, frozen=True, slots=True)
class AgdaVersion:
    _major: int
    _minor: int
    _patch: int
    _build: int
    _prerelease: str = ''

    def __str__(self) -> str:
        return "Agda version %s.%s.%s.%s%s" % (
            self._major, self._minor, self._patch, self._build, (("-%s" % self._prerelease) if self._prerelease else ''))

    @staticmethod
    def parse(text: str) -> AgdaVersion:
        '''Parse an Agda version string of the form 'Agda version X.Y.Z.W-ABC'.'''
        parts = text[12:].split("-")
        version = [int(c) for c in parts[0].split('.')]
        version = version + [0]*max(0, 4-len(version))
        return AgdaVersion(*version, _prerelease=parts[1] if len(parts) > 1 else '')
