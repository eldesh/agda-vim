from functools import total_ordering

@total_ordering
class AgdaVersion:
    _major: int
    _minor: int
    _patch: int
    _build: int
    _prerelease: str

    def __init__(self, major, minor, patch, build, prerelease = ''):
        self._major = major
        self._minor = minor
        self._patch = patch
        self._build = build
        self._prerelease = prerelease

    def __eq__(self, other) -> bool:
        return (self._major, self._minor, self._patch, self._build, self._prerelease) == (other._major, other._minor, other._patch, other._build, other._prerelease)

    def __lt__(self, other) -> bool:
        if (self._major, self._minor, self._patch, self._build) < (other._major, other._minor, other._patch, other._build):
            return True
        if (other._major, other._minor, other._patch, other._build) < (self._major, self._minor, self._patch, self._build):
            return False
        if self._prerelease.is_empty():
            return False
        if other._prerelease.is_empty():
            return True
        return self._prerelease < other._prerelease

    def __str__(self) -> str:
        if self._prerelease:
            return f"Agda version {self._major}.{self._minor}.{self._patch}.{self._build}-{self._prerelease}"
        return f"Agda version {self._major}.{self._minor}.{self._patch}.{self._build}"

    @classmethod
    def parse(cls, text: str) -> 'AgdaVersion':
        '''Parse an Agda version string of the form 'Agda version X.Y.Z.W-ABC'.'''
        parts = text[12:].split("-")
        version = [int(c) for c in parts[0].split('.')]
        version = version + [0]*max(0, 4-len(version))
        return AgdaVersion(*version, prerelease=parts[1] if len(parts) > 1 else '')

