import vim
import re
from functools import total_ordering
import subprocess
from functools import wraps
from sys import version_info
import logging
from enum import Enum, unique

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
        agdaVersion = [int(c) for c in text[12:].split("-")[0].split('.')]
        agdaVersion = agdaVersion + [0]*max(0, 4-len(agdaVersion))
        return AgdaVersion(*agdaVersion)


@unique
class RewriteMode(Enum):
    AsIs = "AsIs"
    Normalised = "Normalised"
    Simplified = "Simplified"
    HeadNormal = "HeadNormal"
    Instantiated = "Instantiated"

    @classmethod
    def parse(cls, text: str) -> 'RewriteMode':
        if cls.AsIs.value == text:
            return cls.AsIs
        elif cls.Normalised.value == text:
            return cls.Normalised
        elif cls.Simplified.value == text:
            return cls.Simplified
        elif cls.HeadNormal.value == text:
            return cls.HeadNormal
        elif cls.Instantiated.value == text:
            return cls.Instantiated
        else:
            raise ValueError("Unknown RewriteMode: %s" % text)


class AgdaProcess:
    _process: subprocess.Popen
    _path: str

    def __init__(self, path: str) -> 'AgdaProcess':
        self._path = path
        self._process = subprocess.Popen(
            [self._path, "--interaction"],
            bufsize = 1,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            universal_newlines = True
        )

    @property
    def path(self) -> str:
        return self._path

    @property
    def stdin(self):
        return self._process.stdin

    @property
    def stdout(self):
        return self._process.stdout

    def restart(self, path):
        '''Terminates the current Agda process and starts a new one located at `path`.'''
        self.stopWait()
        self._path = path
        self._process = subprocess.Popen(
            [self._path, "--interaction"],
            bufsize = 1,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            universal_newlines = True
        )

    def stopWait(self):
        '''Terminates the current Agda process and waits for it to exit. If it does not exit within 10 seconds, it is killed.'''
        sendCommand('Cmd_exit')
        try:
            self._process.wait(timeout = 10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()
        self._process = None
        self._path = None


python_cmd = 'py' if version_info.major == 2 else 'py3'

logger = logging.getLogger('agda.py')
logging.basicConfig(level=logging.WARNING)
logger.setLevel(logging.WARNING)

def logging_level_from_str(x):
    if x is None:
        return None
    try:
        return int(x)
    except ValueError:
        return getattr(logging, x, None)


def logging_level_from(x):
    return logging_level_from_str(x.decode('utf-8') if isinstance(x, bytes) else x)


def vim_func(vim_fname_or_func=None, conv=None):
    '''Expose a python function to vim, optionally overriding its name.'''

    def wrap_func(func, vim_fname, conv):
        fname = func.__name__
        vim_fname = vim_fname or fname
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
        arg_defaults = dict(zip(arg_names[:-len(func.__defaults__ or ()):], func.__defaults__ or []))

        @wraps(func)
        def from_vim(vim_arg_dict):
            args = {}
            for k in arg_names:
                try:
                    val = vim_arg_dict[k]
                except KeyError:
                    val = arg_defaults[k]

                if k in conv:
                    val = conv[k](val)

                args[k] = val
            return func(**args)

        setattr(func, 'from_vim', from_vim)

        vim.command('''
            function! {vim_fname}({vim_params})
                {python_cmd} {fname}.from_vim(vim.eval(\'a:\'))
            endfunction
        '''.format(
            python_cmd=python_cmd,
            vim_fname=vim_fname,
            vim_params=', '.join(arg_names),
            fname=fname,
        ))
        return func

    if callable(vim_fname_or_func):
        return wrap_func(func=vim_fname_or_func, vim_fname=None, conv={})

    def wrapper(func):
        return wrap_func(func=func, vim_fname=vim_fname_or_func, conv=conv or {})
    return wrapper


def vim_bool(s):
    if not s:
        return False
    elif s == 'False':
        return False
    elif s == 'True':
        return True
    return bool(int(s))


# start Agda
# TODO: I'm pretty sure this will start an agda process per buffer which is less than desirable...
agda = None

goals = {}
annotations = []

agdaVersion = AgdaVersion(0, 0, 0, 0)

rewriteMode = RewriteMode.Normalised

# This technically needs to turn a string into a Haskell escaped string, buuuut just gonna cheat.
def escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n','\\n') # keep '\\' case first

# This technically needs to turn a Haskell escaped string into a string, buuuut just gonna cheat.
def unescape(s):
    return s.replace('\\\\','\x00').replace('\\"', '"').replace('\\n','\n').replace('\x00', '\\') # hacktastic

def setRewriteMode(mode):
    global rewriteMode
    try:
        rewriteMode = RewriteMode.parse(mode)
    except ValueError:
        rewriteMode = RewriteMode.Normalised

def promptUser(msg):
    vim.command('call inputsave()')
    result = vim.eval('input("%s")' % msg)
    vim.command('call inputrestore()')
    return result


def findGoals(goalList):
    global goals

    logger.debug("findGoals(%s)" % goalList)
    vim.command('syn sync fromstart') # TODO: This should become obsolete given good sync rules in the syntax file.

    goals = {}
    lines = vim.current.buffer
    row = 1
    agdaHolehlID = vim.eval('hlID("agdaHole")')
    logger.debug("agdaHolehlID: %s" % agdaHolehlID)
    for line in lines:
        line_bytes = line.encode('utf-8')

        start = 0
        while start != -1:
            qstart = line_bytes.find(b"?", start)
            if qstart != -1:
                logger.debug("%d: line_bytes[qstart:]: %d: %s" % (row, qstart, line_bytes[qstart:].decode('utf-8')))
            hstart = line_bytes.find(b"{!", start)
            if hstart != -1:
                logger.debug("%d: line_bytes[hstart:]: %d: %s" % (row, hstart, line_bytes[hstart:].decode('utf-8')))
            if qstart != -1 or hstart != -1:
                logger.debug("line[%d:]:%s" % (start, line))
                logger.debug("(qstart, hstart): (%d,%d)" % (qstart, hstart))
            if qstart == -1:
                start = hstart
            elif hstart == -1:
                start = qstart
            else:
                start = min(hstart, qstart)
            if start != -1:
                start = start + 1

                synID = vim.eval('synID("%d", "%d", 0)' % (row, start))
                logger.debug("synID(%d,%d) = %s" % (row, start, synID))
                if synID == agdaHolehlID:
                    logger.debug("goalList: %s" % goalList)
                    logger.debug("goalList[0]: %s" % goalList[0])
                    logger.debug("goals[goalList.pop(0)] = (%d,%d)" % (row, start))
                    goals[goalList.pop(0)] = (row, start)
                    logger.debug("goals: %s" % goals)
            if len(goalList) == 0: break
        if len(goalList) == 0: break
        row = row + 1

    vim.command('syn sync clear') # TODO: This wipes out any sync rules and should be removed if good sync rules are added to the syntax file.

def findGoal(row, col):
    global goals
    for item in goals.items():
        logger.debug('item[1][0]: %s' % item[1][0])
        logger.debug('item[1][1]: %s' % item[1][1])
        if item[1][0] == row and item[1][1] == col:
            logger.debug('findGoal (found) in %s: (%d,%d)' % (item, row, col))
            return item[0]
    logger.debug('findGoal (not found) in %s: (%d,%d)' % (goals, row, col))
    return None

def getOutput():
    line = agda.stdout.readline()[7:] # get rid of the "Agda2> " prompt
    lines = []
    while not line.startswith('Agda2> cannot read') and line != "":
        lines.append(line)
        line = agda.stdout.readline()
    return lines

# This is not very efficient presumably.
def c2b(n):
    return int(vim.eval('byteidx(join(getline(1, "$"), "\n"),%d)' % n))

# See https://github.com/agda/agda/blob/323f58f9b8dad239142ed1dfa0c60338ea2cb157/src/data/emacs-mode/annotation.el#L112
def parseAnnotation(spans):
    global annotations
    anns = re.findall(r'\((\d+) (\d+) \([^\)]*\) \w+ \(\"([^"]*)\" \. (\d+)\)\)', spans)
    # TODO: This is assumed to be in sorted order.
    logger.debug('parseAnnotation: %s' % anns)
    for ann in anns:
        annotations.append([c2b(int(ann[0])-1), c2b(int(ann[1])-1), ann[2], c2b(int(ann[3]))])

def searchAnnotation(lo, hi, idx):
    global annotations
    logger.debug('searchAnnotation: annotations=%s lo=%d hi=%d idx=%d' % (annotations, lo, hi, idx))

    if hi == 0: return None

    while hi - lo > 1:
        mid = lo + (hi - lo) // 2
        midOffset = annotations[mid][0]
        if idx < midOffset:
            hi = mid
        else:
            lo = mid

    (loOffset, hiOffset) = annotations[lo][0:2]
    if idx > loOffset and idx <= hiOffset:
        return annotations[lo][2:4]
    else:
        return None

def gotoAnnotation():
    global annotations
    byteOffset = int(vim.eval('line2byte(line(".")) + col(".") - 1'))
    result = searchAnnotation(0, len(annotations), byteOffset)
    if result is None: return
    (file, pos) = result
    targetBuffer = None
    for buffer in vim.buffers:
        if buffer.name == file: targetBuffer = buffer.number

    if targetBuffer is None:
        vim.command('edit %s' % file)
    else:
        vim.command('buffer %s' % targetBuffer)
    vim.command('%dgo' % pos)

def interpretResponse(responses, quiet = False):
    global agdaVersion
    for response in responses:
        logger.debug('response: %s' % response)
        if response.startswith('(agda2-info-action ') or response.startswith('(agda2-info-action-and-copy '):
            tag = '(agda2-info-action ' if response.startswith('(agda2-info-action ') else '(agda2-info-action-and-copy '
            if quiet and '*Error*' in response: vim.command('cwindow')
            strings = re.findall(r'"((?:[^"\\]|\\.)*)"', response[len(tag):])
            if strings[0] == '*Agda Version*':
                agdaVersion = AgdaVersion.parse(strings[1])
                logger.debug('AgdaVersion: %s' % agdaVersion)
            if quiet: continue
            vim.command('call s:LogAgda("%s","%s","%s")'% (strings[0], strings[1], response.endswith('t)')))
        elif "(agda2-goals-action '" in response:
            findGoals([int(s) for s in re.findall(r'(\d+)', response[response.index("agda2-goals-action '")+21:])])
        elif "(agda2-make-case-action-extendlam '" in response:
            response = response.replace("?", "{!   !}") # this probably isn't safe
            cases = re.findall(r'"((?:[^"\\]|\\.)*)"', response[response.index("agda2-make-case-action-extendlam '")+34:])
            col = vim.current.window.cursor[1]
            line = vim.current.line

            # TODO: The following logic is far from perfect.
            # Look for a semicolon ending the previous case.
            correction = 0
            starts = [mo for mo in re.finditer(r';', line[:col])]
            if len(starts) == 0:
                # Look for the starting bracket of the extended lambda..
                correction = 1
                starts = [mo for mo in re.finditer(r'{[^!]', line[:col])]
                if len(starts) == 0:
                    # Assume the case is on a line by itself.
                    correction = 1
                    starts = [mo for mo in re.finditer(r'^[ \t]*', line[:col])]
            start = starts[-1].end() - correction

            # Look for a semicolon ending this case.
            correction = 0
            ends = re.search(r';', line[col:])
            if ends == None:
                # Look for the ending bracket of the extended lambda.
                correction = 1
                ends = re.search(r'[^!]}', line[col:])
                if ends == None:
                    # Assume the case is on a line by itself (or at least has nothing after it).
                    correction = 0
                    ends = re.search(r'[ \t]*$', line[col:])
            end = ends.start() + col + correction

            vim.current.line = line[:start] + " " + "; ".join(cases) + " " + line[end:]
            f = vim.current.buffer.name
            sendCommandLoad(f, quiet)
            break
        elif "(agda2-make-case-action '" in response:
            logger.debug('response(bytes): %s' % response.encode('utf-8'))
            response = response.replace("?", "{!   !}") # this probably isn't safe
            cases = re.findall(r'"((?:[^"\\]|\\.)*)"', response[response.index("agda2-make-case-action '")+24:])
            row = vim.current.window.cursor[0]
            logger.debug('row: %s' % row)
            prefix = re.match(r'[ \t]*', vim.current.line).group()
            logger.debug('prefix: "%s"' % prefix)
            vim.current.buffer[row-1:row] = [prefix + case for case in cases]
            logger.debug('vim.current.buffer[%d]: %s' % (row-1, vim.current.buffer[row-1]))
            f = vim.current.buffer.name
            logger.debug('f: %s' % f)
            sendCommandLoad(f, quiet)
            break
        elif response.startswith('(agda2-give-action '):
            response = response.replace("?", "{!   !}")
            logger.debug('response: %s' % response)
            logger.debug('response(bytes): %s' % response.encode('utf-8'))
            match = re.search(r'(\d+)\s+"((?:[^"\\]|\\.)*)"', response[19:])
            logger.debug('match: %s' % match)
            logger.debug('match.group(2): %s' % match.group(2))
            replaceHole(unescape(match.group(2)))
        # elif response.startswith('(agda2-highlight-clear)'):
            # pass # Maybe do something with this.
        elif response.startswith('(agda2-highlight-add-annotations '):
            parseAnnotation(response)
        else:
            pass # print(response)

def sendCommand(arg, quiet=False):
    vim.command('silent! write')
    f = vim.current.buffer.name
    logger.debug('sendCommand(%s)' % f)
    # The x is a really hacky way of getting a consistent final response.  Namely, "cannot read"
    agda.stdin.write('IOTCM "%s" None Direct (%s)\nx\n' % (escape(f), arg))
    logger.debug('IOTCM "%s" None Direct (%s)\nx\n' % (escape(f), arg))
    interpretResponse(getOutput(), quiet)

def sendCommandLoadHighlightInfo(file, quiet):
    sendCommand('Cmd_load_highlighting_info "%s"' % escape(file), quiet = quiet)

def sendCommandLoad(file, quiet):
    global agdaVersion
    if agdaVersion < AgdaVersion(2,5,0,0): # in 2.5 they changed it so Cmd_load takes commandline arguments
        incpaths_str = ",".join(map(lambda x: x.decode('utf-8'), vim.vars['agdavim_agda_includepathlist']))
    else:
        incpaths_str = "\"-i\"," + ",\"-i\",".join(map(lambda x: x.decode('utf-8'), vim.vars['agdavim_agda_includepathlist']))
    sendCommand('Cmd_load "%s" [%s]' % (escape(file), incpaths_str), quiet = quiet)

#def getIdentifierAtCursor():
#    (r, c) = vim.current.window.cursor
#    line = vim.current.line
#    try:
#        start = re.search(r"[^\s@(){};]+$", line[:c+1]).start()
#        end = re.search(r"^[^\s@(){};]+", line[c:]).end() + c
#    except AttributeError as e:
#        return None
#    return line[start:end]

def replaceHole(replacement):
    logger.debug('replacement: %s' % replacement)
    rep = replacement.replace('\n', ' ').replace('    ', ';') # TODO: This probably needs to be handled better
    (r, c) = vim.current.window.cursor
    line = vim.current.line
    line_bytes = line.encode('utf-8')
    c_str = len(line_bytes[:c].decode('utf-8'))
    if line_bytes[c] == "?":
        start = c
        end = c+1
    else:
        try:
            mo = None
            for mo in re.finditer(r"{!", line[:min(len(line),c_str+2)]): pass
            start = mo.start()
            end = re.search(r"!}", line[max(0,c_str-1):]).end() + max(0,c_str-1)
        except AttributeError:
            return
    vim.current.line = line[:start] + rep + line[end:]

def getHoleBodyAtCursor():
    (r, c) = vim.current.window.cursor
    line = vim.current.line
    line_bytes = line.encode('utf-8')
    logger.debug('getHoleBodyAtCursor: (%s,%s): %s' % (r, c, line))
    logger.debug('line bytes: %d: %s' % (len(line_bytes), line_bytes))
    linesub = line_bytes[:c].decode('utf-8')
    linesub_len = len(linesub)
    pos = linesub_len
    logger.debug('linesub: %d: %s' % (linesub_len, linesub))
    try:
        logger.debug('line[%d]: %s' % (pos, line[pos]))
        if line[pos] == "?":
            return ("?", findGoal(r, c+1))
    except IndexError:
        logger.debug('getHoleBodyAtCursor: IndexError')
        return None
    try: # handle virtual space better
        mo = None
        for mo in re.finditer(r"{!", line[:min(len(line),pos+2)]): pass
        start = mo.start()
        end = re.search(r"!}", line[max(0,pos-1):]).end() + max(0,pos-1)
        logger.debug('getHoleBodyAtCursor: %s,%d,%d,%s' % (mo, start, end, line[start:end]))
    except AttributeError:
        logger.debug('getHoleBodyAtCursor: AttributeError')
        return None
    result = line[start+2:end-2].strip()
    logger.debug('getHoleBodyAtCursor: result: %d,%d: %s' % (start+2, end-2, result))
    if result == "":
        result = "?"
    return (result, findGoal(r, len(line[:start].encode('utf-8'))+1))


def getWordAtCursor():
    return vim.eval("expand('<cWORD>')").strip()


## Directly exposed functions: {

@vim_func
def AgdaRestartAgda(path):
    '''Tries to start or restart the Agda process.'''
    global agda

    if agda is None:
        logger.info("Starting Agda process with path: %s" % path)
        agda = AgdaProcess(path)
    elif agda.path != path:
        logger.info("Restarting Agda process with new path: %s" % path)
        agda.restart(path)
    else:
        logger.info("Agda process already running with path: %s" % path)

@vim_func
def AgdaQuitAgda():
    '''Quit and clean up after agda2'''
    global agda

    if agda:
        agda.swtopWait()
        agda = None

@vim_func(conv={'quiet': vim_bool})
def AgdaShowVersion(quiet):
    sendCommand('Cmd_show_version', quiet=quiet)


@vim_func(conv={'quiet': vim_bool})
def AgdaLoad(quiet):
    f = vim.current.buffer.name
    sendCommandLoad(f, quiet)
    if vim.vars['agdavim_enable_goto_definition']:
        sendCommandLoadHighlightInfo(f, quiet)


@vim_func(conv={'quiet': vim_bool})
def AgdaLoadHighlightInfo(quiet):
    f = vim.current.buffer.name
    sendCommandLoadHighlightInfo(f, quiet)


@vim_func
def AgdaGotoAnnotation():
    gotoAnnotation()


@vim_func
def AgdaGive():
    result = getHoleBodyAtCursor()

    if agdaVersion < AgdaVersion(2,5,3,0):
        useForce = ""
    else:
        useForce = "WithoutForce" # or WithForce

    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "?":
        sendCommand('Cmd_give %s %d noRange "%s"' % (useForce, result[1], escape(promptUser("Enter expression: "))))
    else:
        sendCommand('Cmd_give %s %d noRange "%s"' % (useForce, result[1], escape(result[0])))


@vim_func
def AgdaMakeCase():
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "?":
        sendCommand('Cmd_make_case %d noRange "%s"' % (result[1], escape(promptUser("Make case on: "))))
    else:
        sendCommand('Cmd_make_case %d noRange "%s"' % (result[1], escape(result[0])))


@vim_func
def AgdaRefine(unfoldAbstract):
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_refine_or_intro %s %d noRange "%s"' % (unfoldAbstract, result[1], escape(result[0])))


@vim_func
def AgdaAuto():
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        if agdaVersion < AgdaVersion(2,6,0,0):
            sendCommand('Cmd_auto %d noRange "%s"' % (result[1], escape(result[0]) if result[0] != "?" else ""))
        else:
            sendCommand('Cmd_autoOne %d noRange "%s"' % (result[1], escape(result[0]) if result[0] != "?" else ""))


@vim_func
def AgdaContext():
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_goal_type_context_infer %s %d noRange "%s"' % (rewriteMode.value, result[1], escape(result[0])))


@vim_func
def AgdaInfer():
    result = getHoleBodyAtCursor()
    if result is None:
        sendCommand('Cmd_infer_toplevel %s "%s"' % (rewriteMode.value, escape(promptUser("Enter expression: "))))
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_infer %s %d noRange "%s"' % (rewriteMode.value, result[1], escape(result[0])))


# As of 2.5.2, the options are "DefaultCompute", "IgnoreAbstract", "UseShowInstance"
@vim_func
def AgdaNormalize(unfoldAbstract):
    if agdaVersion < AgdaVersion(2,5,2,0):
        unfoldAbstract = str(unfoldAbstract == "DefaultCompute")

    result = getHoleBodyAtCursor()
    if result is None:
        sendCommand('Cmd_compute_toplevel %s "%s"' % (unfoldAbstract, escape(promptUser("Enter expression: "))))
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_compute %s %d noRange "%s"' % (unfoldAbstract, result[1], escape(result[0])))


@vim_func
def AgdaWhyInScope(termName):
    result = getHoleBodyAtCursor() if termName == '' else None

    if result is None:
        termName = getWordAtCursor() if termName == '' else termName
        termName = promptUser("Enter name: ") if termName == '' else termName
        sendCommand('Cmd_why_in_scope_toplevel "%s"' % escape(termName))
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_why_in_scope %d noRange "%s"' % (result[1], escape(result[0])))


@vim_func
def AgdaMetas(mode = None):
    if mode is None:
        rewriteMode = RewriteMode.Normalised
    try:
        rewriteMode = RewriteMode.parse(mode)
    except ValueError:
        rewriteMode = RewriteMode.Normalised
    sendCommand('Cmd_metas %s' % rewriteMode.value)


@vim_func
def AgdaShowModule(moduleName):
    result = getHoleBodyAtCursor() if moduleName == '' else None

    if agdaVersion < AgdaVersion(2,4,2,0):
        if result is None:
            moduleName = promptUser("Enter module name: ") if moduleName == '' else moduleName
            sendCommand('Cmd_show_module_contents_toplevel "%s"' % escape(moduleName))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_show_module_contents %d noRange "%s"' % (result[1], escape(result[0])))
    else:
        if result is None:
            moduleName = promptUser("Enter module name: ") if moduleName == '' else moduleName
            sendCommand('Cmd_show_module_contents_toplevel %s "%s"' % (rewriteMode.value, escape(moduleName)))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_show_module_contents %s %d noRange "%s"' % (rewriteMode.value, result[1], escape(result[0])))


@vim_func
def AgdaHelperFunction():
    result = getHoleBodyAtCursor()

    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "?":
        sendCommand('Cmd_helper_function %s %d noRange "%s"' % (rewriteMode.value, result[1], escape(promptUser("Enter name for helper function: "))))
    else:
        sendCommand('Cmd_helper_function %s %d noRange "%s"' % (rewriteMode.value, result[1], escape(result[0])))

@vim_func
def AgdaVimSetLoggingLevel(level):
    logger.setLevel(level)
    logging.basicConfig(level=level)
    print("Set logging level to %s" % logging.getLevelName(level))

@vim_func
def AgdaRunningPath():
    return agda.path

## }
