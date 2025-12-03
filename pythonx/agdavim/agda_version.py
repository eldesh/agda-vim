from functools import total_ordering

@total_ordering
class AgdaVersion:
    _major: int
    _minor: int
    _patch: int
    _build: int

    def __init__(self, major, minor, patch, build):
        self._major = major
        self._minor = minor
        self._patch = patch
        self._build = build

    def __eq__(self, other) -> bool:
        return (self._major, self._minor, self._patch, self._build) == (other._major, other._minor, other._patch, other._build)

    def __lt__(self, other) -> bool:
        return (self._major, self._minor, self._patch, self._build) < (other._major, other._minor, other._patch, other._build)

    def __str__(self) -> str:
        return f"{self._major}.{self._minor}.{self._patch}.{self._build}"

    @classmethod
    def parse(cls, text: str) -> 'AgdaVersion':
        '''Parse an Agda version string of the form 'Agda version X.Y.Z.W-ABC'.'''
        version = [int(c) for c in text[12:].split("-")[0].split('.')]
        version = version + [0]*max(0, 4-len(version))
        return AgdaVersion(*version)

