import vim
import re
import logging
from sys import version_info
from functools import wraps
from itertools import chain
from typing import Iterator, Tuple, List, Optional

from .agda_process import AgdaProcess
from .agda_version import AgdaVersion
from .protocol import ComputeMode, NormaliseType, NormaliseAsIsType
from . import log
from . import response
from .response import FilePosition, InfoActionResponse, InfoActionAndCopyResponse, GoalsActionResponse, GiveActionResponse, MakeCaseActionResponse, MakeCaseActionExtendlamResponse, HighlightAddAnnotationsResponse, HighlightAnnotation, GiveString, RemoveTokenBasedHighlighting
from .response import sexpr

python_cmd = 'py' if version_info.major == 2 else 'py3'

logger = logging.getLogger(__name__)

AGDA2_OUTPUT_PROMPT: str = "Agda2> "



class HighlightCommand:
    _from: int
    _to: int
    _aspects: List[str]
    _token_based: bool
    _info: Optional[str]
    _filepos: Optional[FilePosition]

    def __init__(self, from_: int, to: int, aspects: List[str],
                 token_based: bool,
                 info: Optional[str],
                 filepos: Optional[FilePosition]):
        self._from = from_
        self._to = to
        self._aspects = aspects
        self._token_based = token_based
        self._info = info
        self._filepos = filepos

    def __str__(self):
        return "(from=%d, to=%d, aspects=%s, token_based=%s, info=%s, filepos=%s)" % (
            self._from, self._to, self._aspects, self._token_based, self._info, self._filepos)

    @property
    def from_(self) -> int:
        return self._from

    @property
    def to(self) -> int:
        return self._to

    @property
    def aspects(self) -> List[str]:
        return self._aspects

    @property
    def token_based(self) -> bool:
        return self._token_based

    @property
    def info(self) -> Optional[str]:
        return self._info

    @property
    def filepos(self) -> Optional[FilePosition]:
        return self._filepos


class AddHighlightCommand(HighlightCommand):
    pass


class RemoveHighlightCommand(HighlightCommand):
    pass


def highlight_cmds_from_response(resp: HighlightAddAnnotationsResponse) -> Iterator[HighlightCommand]:
    if resp.removeHighlighting == RemoveTokenBasedHighlighting.RemoveHighlighting:
        for ann in resp.annotations:
            yield RemoveHighlightCommand(c2b(ann.from_-1), c2b(ann.to-1), ann.aspects,
                                         ann.token_based is True, ann.info if ann.info is sexpr.NIL else ann.info,
                                         FilePosition(ann.filepos.file, c2b(ann.filepos.pos-1)) if ann.filepos is not None else None)
    else:
        for ann in resp.annotations:
            yield AddHighlightCommand   (c2b(ann.from_-1), c2b(ann.to), ann.aspects,
                                         ann.token_based is True, ann.info if ann.info is sexpr.NIL else ann.info,
                                         FilePosition(ann.filepos.file, c2b(ann.filepos.pos-1)) if ann.filepos is not None else None)


def vim_func(vim_fname_or_func=None, conv=None):
    '''Expose a python function to vim, optionally overriding its name.'''

    def wrap_func(func, vim_fname, conv):
        module = func.__module__
        fname = func.__name__
        vim_fname = vim_fname or fname
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
        arg_defaults = list(zip(arg_names[-len(func.__defaults__ or ()):], func.__defaults__ or []))
        defaults_len = len(func.__defaults__ or ())

        @wraps(func)
        def from_vim(vim_arg_dict):
            '''Convert vim arguments to python and call the function.'''
            logger.debug("vim_arg_dict: %s" % vim_arg_dict)
            args = {}
            # Handle non-defaulted arguments.
            for k in arg_names[:-defaults_len]:
                val = vim_arg_dict[k]
                if k in conv:
                    val = conv[k](val)
                args[k] = val
            # Handle defaulted arguments.
            for i, k in enumerate(arg_names[-defaults_len:]):
                try:
                    val = vim_arg_dict[k]
                except KeyError:
                    _key, val = arg_defaults[i]
                if k in conv:
                    val = conv[k](val)
                args[k] = val
            return func(**args)

        func.from_vim = from_vim

        vim_params = chain(arg_names[0:len(arg_names) - defaults_len], ['...'] if defaults_len > 0 else [])
        vimfunc_def = '''
            function! {vim_fname}({vim_signature})
                {python_cmd} {module}.{fname}.from_vim(vim.eval(\'a:\'))
            endfunction
        '''.format(
            python_cmd=python_cmd,
            vim_fname=vim_fname,
            vim_signature=', '.join(vim_params),
            fname=fname,
            module=module
        )
        #print("vimfunc_def: %s" % vimfunc_def)
        vim.command(vimfunc_def)
        return func

    if callable(vim_fname_or_func):
        return wrap_func(func=vim_fname_or_func, vim_fname=None, conv={})

    def wrapper(func):
        return wrap_func(func=func, vim_fname=vim_fname_or_func, conv=conv or {})
    return wrapper


def vim_bool(s):
    if isinstance(s, bool):
        return s
    if s == 'False':
        return False
    if s == 'True':
        return True
    raise ValueError("Cannot convert %s to bool" % s)

def vim_int_range(start, stop, step = 1):
    r = range(start, stop, step)
    def inner(s):
        val = int(s)
        if val in r:
            return val
        raise ValueError("Value %s is not in range %s" % (val, r))
    return inner

def vim_compute_mode(s):
    return ComputeMode.from_int(int(s))

def vim_normalise(s):
    return NormaliseType.from_int(int(s))

def vim_normalise_asis(s):
    return NormaliseAsIsType.from_int(int(s))

# start Agda
# TODO: I'm pretty sure this will start an agda process per buffer which is less than desirable...
agda = None

goals = {}
annotations = []

# This technically needs to turn a string into a Haskell escaped string, buuuut just gonna cheat.
def escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n','\\n') # keep '\\' case first

# This technically needs to turn a Haskell escaped string into a string, buuuut just gonna cheat.
def unescape(s):
    return s.replace('\\\\','\x00').replace('\\"', '"').replace('\\n','\n').replace('\x00', '\\') # hacktastic

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


def getOutput() -> Iterator[response.Response]:
    line = agda.stdout.readline()
    if not line.startswith(AGDA2_OUTPUT_PROMPT):
        logger.warning("Unexpected Agda output: not startswith %s: %s" % (AGDA2_OUTPUT_PROMPT, line))
    else:
        line = line[len(AGDA2_OUTPUT_PROMPT):]

    while not line.startswith('Agda2> cannot read') and line != "":
        yield response.parse_response(line)
        line = agda.stdout.readline()


# This is not very efficient presumably.
def c2b(n):
    '''Convert a character index to a byte index in the current buffer.'''
    return int(vim.eval('byteidx(join(getline(1, "$"), "\n"),%d)' % n))

# See https://github.com/agda/agda/blob/323f58f9b8dad239142ed1dfa0c60338ea2cb157/src/data/emacs-mode/annotation.el#L112
def parseAnnotation(response):
    global annotations
    annotations += list(highlight_cmds_from_response(response))
    logger.debug('annotations: %s' % annotations)


def searchAnnotation(lo, hi, idx):
    logger.debug('searchAnnotation: annotations=%s lo=%d hi=%d idx=%d' % (annotations, lo, hi, idx))

    if hi == 0: return None

    while hi - lo > 1:
        mid = lo + (hi - lo) // 2
        midOffset = annotations[mid].from_
        if idx < midOffset:
            hi = mid
        else:
            lo = mid

    (loOffset, hiOffset) = (annotations[lo].from_, annotations[lo].to)
    if idx > loOffset and idx <= hiOffset:
        return annotations[lo].filepos.as_tuple
    else:
        return None

def gotoAnnotation():
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
    global agda
    for response in responses:
        logger.debug('response: %s' % response)
        if isinstance(response, InfoActionResponse) or isinstance(response, InfoActionAndCopyResponse):
            if quiet and '*Error*' == response.name: vim.command('cwindow')
            strings = [response.name, response.text]
            if strings[0] == '*Agda Version*':
                agda_mode_version = AgdaVersion.parse(strings[1])
                logger.debug('AgdaVersion: mode(%s) executable(%s)' % (agda_mode_version, agda.version))
                if agda.version != agda_mode_version:
                    logger.error('Agda mode\'s version (%s) does not match that of %s (%s)'
                                 % (agda_mode_version, agda.path, agda.version))
            if quiet: continue
            vim.command('call s:LogAgda("%s","%s",%s)' % (strings[0], strings[1], 'v:true' if response.append else 'v:false'))

        elif isinstance(response, GoalsActionResponse):
            findGoals(response.goals)

        elif isinstance(response, MakeCaseActionExtendlamResponse):
            newcls = [ cls.replace("?", "{!   !}") for cls in response.newcls ] # this probably isn't safe

            # ss = ' \'("z {true} → ?" "z {false} → ?")))'
            # >>> re.findall(r'"((?:[^"\\]|\\.)*)"', ss)
            # ['z {true} → ?', 'z {false} → ?']
            cases = newcls

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

        elif isinstance(response, MakeCaseActionResponse):
            newcls = [ cls.replace("?", "{!   !}") for cls in response.newcls ] # this probably isn't safe
            cases = newcls
            row = vim.current.window.cursor[0]
            prefix = re.match(r'[ \t]*', vim.current.line).group()
            vim.current.buffer[row-1:row] = [prefix + case for case in cases]
            f = vim.current.buffer.name
            sendCommandLoad(f, quiet)
            break

        elif isinstance(response, GiveActionResponse):
            giveResult = GiveString(response.giveResult.text.replace("?", "{!   !}")) \
                if isinstance(response.giveResult, GiveString) else response.giveResult
            replaceHole(unescape("%s" % giveResult))

        # elif response.startswith('(agda2-highlight-clear)'):
            # pass # Maybe do something with this.
        elif isinstance(response, HighlightAddAnnotationsResponse):
            parseAnnotation(response)

        else:
            pass # print(response)

def sendCommand(arg, quiet=False):
    vim.command('silent! write')
    f = vim.current.buffer.name
    logger.debug('IOTCM "%s" None Direct (%s)\nx\n' % (escape(f), arg))
    # The x is a really hacky way of getting a consistent final response.  Namely, "cannot read"
    agda.stdin.write('IOTCM "%s" None Direct (%s)\nx\n' % (escape(f), arg))
    interpretResponse(getOutput(), quiet)

def sendCommandLoadHighlightInfo(file, quiet):
    sendCommand('Cmd_load_highlighting_info "%s"' % escape(file), quiet = quiet)

def sendCommandLoad(file, quiet):
    if agda.version < AgdaVersion(2,5,0,0): # in 2.5 they changed it so Cmd_load takes commandline arguments
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
    if line_bytes[c] == ord("?"):
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
    return (result, findGoal(r, len(line[:start].encode('utf-8'))+1))


def getWordAtCursor():
    return vim.eval("expand('<cword>')").strip()


## Directly exposed functions: {

@vim_func
def AgdaRestartAgda(path):
    '''Tries to start or restart the Agda process.'''
    global agda

    if agda is None:
        logger.info("Starting Agda process with path: %s" % path)
        agda = AgdaProcess(path)
    else:
        logger.info("Restarting Agda process with new path: %s" % path)
        agda.restart(path)

@vim_func
def AgdaQuitAgda():
    '''Quit and clean up after agda2'''
    global agda

    if agda:
        logger.info("Stopping Agda process")
        agda.stop_wait()
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

@vim_func(conv={'arg': vim_int_range(0,3)})
def AgdaDisplayImplicitArguments(arg: int):
    if arg == 0:
        return sendCommand('ToggleImplicitArgs')
    if arg == 1:
        return sendCommand('ShowImplicitArgs True')
    if arg == 2:
        return sendCommand('ShowImplicitArgs False')

@vim_func
def AgdaGive():
    result = getHoleBodyAtCursor()

    if agda.version < AgdaVersion(2,5,3,0):
        useForce = ""
    else:
        useForce = "WithoutForce" # or WithForce

    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "?":
        sendCommand('Cmd_give %s %d noRange "%s"' % (useForce, result[1], escape(promptUser("expression to give: "))))
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
        prompt = "pattern variables to case (empty for split on result): "
        sendCommand('Cmd_make_case %d noRange "%s"' % (result[1], escape(promptUser(prompt))))
    else:
        sendCommand('Cmd_make_case %d noRange "%s"' % (result[1], escape(result[0])))


@vim_func(conv={'pmlambda': vim_bool})
def AgdaRefine(pmlambda):
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_refine_or_intro %s %d noRange "%s"' % (pmlambda, result[1], escape(result[0])))


@vim_func
def AgdaAuto():
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        if agda.version < AgdaVersion(2,6,0,0):
            sendCommand('Cmd_auto %d noRange "%s"' % (result[1], escape(result[0]) if result[0] != "?" else ""))
        else:
            sendCommand('Cmd_autoOne %d noRange "%s"' % (result[1], escape(result[0]) if result[0] != "?" else ""))


@vim_func(conv={'normalise': vim_normalise})
def AgdaGoalAndContext(normalise):
    '''Shows the type of the goal at point and the current context'''
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_goal_type_context %s %d noRange "%s"' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaGoalAndContextAndInferred(normalise):
    '''Shows the context, the goal and the given expression's inferred type'''
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "":
        prompt = promptUser("expression to type: ")
        sendCommand('Cmd_goal_type_context_infer %s %d noRange "%s"' % (normalise.name, result[1], escape(prompt)))
    else:
        sendCommand('Cmd_goal_type_context_infer %s %d noRange "%s"' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaGoalAndContextAndChecked(normalise):
    '''Shows the context, the goal and check the given expression's against the hole's type'''
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "":
        prompt = promptUser("expression to type: ")
        sendCommand('Cmd_goal_type_context_check %s %d noRange "%s"' % (normalise.name, result[1], escape(prompt)))
    else:
        sendCommand('Cmd_goal_type_context_check %s %d noRange "%s"' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaShowContext(normalise):
    '''Show the context of the goal at point'''
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_context %s %d noRange "%s"' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaInferTypeMaybeToplevel(normalise):
    result = getHoleBodyAtCursor()
    if result is None:
        sendCommand('Cmd_infer_toplevel %s "%s"' % (normalise.name, escape(promptUser("expression to type: "))))
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_infer %s %d noRange "%s"' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'computeMode': vim_compute_mode})
def AgdaComputeNormalisedMaybeToplevel(computeMode):
    result = getHoleBodyAtCursor()

    if agda.version < AgdaVersion(2,5,2,0):
        mode = computeMode == ComputeMode.DefaultCompute
        if result is None:
            prompt = promptUser("expression to normalise: ")
            sendCommand('Cmd_compute_toplevel %s "%s"' % (mode, escape(prompt)))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_compute %s %d noRange "%s"' % (mode, result[1], escape(result[0])))
    else:
        if result is None:
            prompt = promptUser("expression to normalise: ")
            sendCommand('Cmd_compute_toplevel %s "%s"' % (computeMode.name, escape(prompt)))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_compute %s %d noRange "%s"' % (computeMode.name, result[1], escape(result[0])))


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


@vim_func(conv={'normalise': vim_normalise})
def AgdaSearchAbout(normalise, name: str = ''):
    '''Search About an identifier.'''
    cname = getWordAtCursor() if name == '' else name
    query = promptUser("Name: ") if cname == '' else cname
    sendCommand('Cmd_search_about_toplevel %s "%s"' % (normalise.name, query))


@vim_func(conv={'normalise': vim_normalise})
def AgdaShowGoals(normalise):
    sendCommand('Cmd_metas %s' % normalise.name)


@vim_func(conv={'normalise': vim_normalise})
def AgdaModuleContentsMaybeToplevel(normalise, moduleName = ''):
    result = getHoleBodyAtCursor() if moduleName == '' else None

    if agda.version < AgdaVersion(2,4,2,0):
        if result is None:
            moduleName = promptUser("Module name (empty for current module): ") if moduleName == '' else moduleName
            sendCommand('Cmd_show_module_contents_toplevel "%s"' % escape(moduleName))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_show_module_contents %d noRange "%s"' % (result[1], escape(result[0])))
    else:
        if result is None:
            moduleName = promptUser("Module name (empty for current module): ") if moduleName == '' else moduleName
            sendCommand('Cmd_show_module_contents_toplevel %s "%s"' % (normalise.name, escape(moduleName)))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_show_module_contents %s %d noRange "%s"' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise_asis})
def AgdaHelperFunctionType(normalise):
    result = getHoleBodyAtCursor()

    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "?":
        sendCommand('Cmd_helper_function %s %d noRange "%s"' % (normalise.name, result[1], escape(promptUser("Expression: "))))
    else:
        sendCommand('Cmd_helper_function %s %d noRange "%s"' % (normalise.name, result[1], escape(result[0])))

@vim_func
def AgdaVimSetLoggingLevel(level):
    log.set_logging_level(level=level)
    print("Set logging level to %s" % level)


## }
