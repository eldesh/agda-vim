import vim
import re
import logging
from typing import Iterator, List, Optional, MutableMapping, Tuple
from dataclasses import dataclass

from .agda_path import escape, unescape, agda2_quote_list
from .agda_process import AgdaProcess
from .agda_version import AgdaVersion
from .agda_goal import AgdaGoal, GoalNumber
from .command import HighlightLevel, Remove as HighlightRemove, HighlightCommand
from . import log
from . import response
from .response import InfoActionResponse, InfoActionAndCopyResponse, GoalsActionResponse, GiveActionResponse, MakeCaseActionResponse, MakeCaseActionExtendlamResponse, HighlightAddAnnotationsResponse, GiveString, RemoveTokenBasedHighlighting
from .response import sexpr
from .vimfunc import vim_func, vim_bool, vim_int_range, vim_normalise, vim_compute_mode, vim_normalise_asis
from .property import AgdaProperty, PropertyId, PropertyKey
from .vimapi import prop_add, prop_remove, prop_list
from . import vimapi
from .response.filepos import OBPoint, OCFilePosition
from .protocol import NormaliseType, ComputeMode


logger = logging.getLogger(__name__)

AGDA2_OUTPUT_PROMPT: str = "Agda2> "


# start Agda
# TODO: I'm pretty sure this will start an agda process per buffer which is less than desirable...
agda = None

agda_goal_set: set[AgdaGoal] = set([])

annotations = []

id_property_map: MutableMapping[PropertyId, AgdaProperty] = {}

property_id_ctx: int = 0


def gen_property_id() -> PropertyId:
    global property_id_ctx
    property_id_ctx += 1
    return PropertyId(property_id_ctx)


def highlight_cmds_from_response(resp: HighlightAddAnnotationsResponse) -> Iterator[HighlightCommand]:
    for ann in resp.annotations:
        yield HighlightCommand(c2b(ann.from_), c2b(ann.to), ann.aspects,
                                ann.token_based is True,
                                None if ann.info is sexpr.NIL else ann.info,
                                ann.filepos)


def promptUser(prompt: str) -> str:
    vimapi.inputsave()
    input = vimapi.input(prompt)
    vimapi.inputrestore()
    return input


def find_goals_from_current_buffer(goals: List[int]) -> Iterator[AgdaGoal]:
    """Find goals in the current buffer.

    Yields:
        Goal objects found in the current buffer.
        '?' is replaced with '{!!}'.
    """
    pattern = re.compile("\\?|{[-!]|[-!]}|--|^%.*\\\\begin{code}|\\\\begin{code}|\\\\end{code}|```|#\\+begin_src agda2|#\\+end_src agda2")

    buffer = vim.current.buffer
    for row, line in enumerate(buffer, start=1):
        for m in pattern.finditer(line):
            logger.debug("found pattern %s at %d:%d" % (m.group(), row, m.start()))
            if m.group() == "?":
                col0 = m.start()
                vim.current.buffer[row-1] = line[:col0] + "{!!}" + line[col0+1:]
                yield AgdaGoal(buffer.number, GoalNumber(goals.pop(0)), vim.current.buffer[row-1][col0:col0+4], OBPoint(row, col0+1), OBPoint(row, col0+1+4))
            elif m.group() == "{!":
                hend = line.find("!}", m.end())
                if hend != -1:
                    col0 = m.start()
                    yield AgdaGoal(buffer.number, GoalNumber(goals.pop(0)), line[col0:hend+2], OBPoint(row, col0+1), OBPoint(row, hend+1+2))


def forget_all_goal_properties():
    global agda_goal_set
    global id_property_map

    agda_goal_set.clear()
    for lnum in range(1, len(vim.current.buffer)+1): # 1-origin
        for prop in prop_list(lnum, { 'types': ['agdavim:agdaHole'] }):
            logger.debug("delete: prop: %s" % prop)
            del id_property_map[PropertyId(int(prop["id"]))]

    prop_remove({ 'type': 'agdavim:agdaHole', 'all': True })
    prop_remove({ 'type': 'agdavim:agdaHoleNumber', 'all': True })


def goal_action(goalList: List[int]):
    global agda_goal_set
    global id_property_map

    logger.debug("goal_action(%s)" % goalList)
    vimapi.command('syn sync fromstart') # TODO: This should become obsolete given good sync rules in the syntax file.
    forget_all_goal_properties()
    for goal in find_goals_from_current_buffer(goalList):
        agda_goal_set.add(goal)
        if goal.contents.startswith("{!") and goal.contents.endswith("!}"):
            logger.debug("goal action: %s" % goal)
            pos = goal.pos_start
            prop_id = gen_property_id()
            length = goal.pos_end.col - goal.pos_start.col
            prop = AgdaProperty({ PropertyKey.GOAL_NUMBER: goal.num, PropertyKey.VIRTUAL_TXT: "%s" % goal.num })
            prop_add(pos.row, pos.col       , {'type': 'agdavim:agdaHole', 'id': prop_id.get(), 'length': length})
            prop_add(pos.row, pos.col+length, {'type': 'agdavim:agdaHoleNumber', 'text': prop[PropertyKey.VIRTUAL_TXT] })
            id_property_map[prop_id] = prop
        else:
            logger.error("unexpected goal: %s" % goal)

    vimapi.command('syn sync clear') # TODO: This wipes out any sync rules and should be removed if good sync rules are added to the syntax file.


def findGoal(row: int, col: int) -> Optional[int]:
    for item in agda_goal_set:
        logger.debug('find goal: %s' % item)
        if item.pos_start == OBPoint(row, col):
            logger.debug('findGoal (found) in %s: (%d,%d)' % (item, row, col))
            return item.num
    logger.debug('findGoal (not found) in %s: (%d,%d)' % (agda_goal_set, row, col))
    return None


def getOutput() -> Iterator[response.Response]:
    if agda is None:
        return
    line = agda.stdout.readline()
    if not line.startswith(AGDA2_OUTPUT_PROMPT):
        logger.warning("Unexpected Agda output: not startswith %s: %s" % (AGDA2_OUTPUT_PROMPT, line))
    else:
        line = line[len(AGDA2_OUTPUT_PROMPT):]

    while not line.startswith('Agda2> cannot read') and line != "":
        yield response.parse_response(line)
        line = agda.stdout.readline()


# This is not very efficient presumably.
def c2b(n: int):
    '''Convert a character index to a byte index in the current buffer.'''
    return int(vim.eval('byteidx(join(getline(1, "$"), "\n"),%d)' % n))

# See https://github.com/agda/agda/blob/323f58f9b8dad239142ed1dfa0c60338ea2cb157/src/data/emacs-mode/annotation.el#L112
def parseAnnotation(response: HighlightAddAnnotationsResponse):
    global annotations
    # if response.removeHighlighting == RemoveTokenBasedHighlighting.RemoveHighlighting:
    #    TODO: Remove token based highlighting
    annotations = list(highlight_cmds_from_response(response))
    # logger.debug('annotations: %s' % ('[' + ' '.join([str(ann) for ann in annotations[:8]]) + ']'))


def searchAnnotation(anns: List[HighlightCommand], idx: int) -> Optional[OCFilePosition]:
    """Search for an annotation covering the given byte index.
    Assumes anns is sorted in ascending order by from_ field.
    """
    # logger.debug('searchAnnotation: %s: %d' % ([ [ann.from_, ann.to, str(ann.filepos)] for ann in annotations[:8] ], idx))

    if not anns:
        return None

    lo = 0
    hi = len(anns)

    while hi - lo > 1:
        mid = lo + (hi - lo) // 2
        if idx < anns[mid].from_:
            hi = mid
        else:
            lo = mid

    if anns[lo].from_ < idx <= anns[lo].to:
        return anns[lo].filepos
    else:
        return None

def gotoAnnotation():
    # Get the byte offset of the current cursor.
    byteOffset = int(vim.eval('line2byte(line(".")) + col(".") - 1'))
    filepos = searchAnnotation(annotations, byteOffset)
    if filepos is None:
        return

    targetBuffer = next(
        (b for b in vim.buffers if b.name == filepos.file),
        None,
    )

    if targetBuffer is None:
        vim.command('edit %s' % filepos.file)
    else:
        vim.command('buffer %s' % targetBuffer.number)
    vim.command('%dgo' % filepos.pos)

def interpretResponse(responses: Iterator[response.Response], quiet: bool = False):
    global agda
    for response in responses:
        logger.debug('response: %s' % response)
        if isinstance(response, InfoActionResponse) or isinstance(response, InfoActionAndCopyResponse):
            if quiet and '*Error*' == response.name: vim.command('cwindow')
            strings = [response.name, response.text]
            if strings[0] == '*Agda Version*':
                agda_mode_version = AgdaVersion.parse(strings[1])
                logger.debug('AgdaVersion: mode(%s) executable(%s)' % (agda_mode_version, agda.version if agda is not None else 'None'))
                if agda and agda.version != agda_mode_version:
                    logger.error('Agda mode\'s version (%s) does not match that of %s (%s)'
                                 % (agda_mode_version, agda.path, agda.version))
            if quiet: continue
            vim.command('call s:LogAgda("%s","%s",%s)' % (strings[0], strings[1], 'v:true' if response.append else 'v:false'))

        elif isinstance(response, GoalsActionResponse):
            goal_action(response.goals)

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

def sendCommand(arg: str, highlight: bool = False, quiet: bool = False):
    vim.command('silent! write')
    f: str = vim.current.buffer.name
    _highlight_level = Agda2HighlightLevel() if highlight else HighlightLevel.NONE
    logger.debug('IOTCM %s %s Indirect (%s)\nx\n' % (escape(f), _highlight_level, arg))
    # The x is a really hacky way of getting a consistent final response.  Namely, "cannot read"
    agda.stdin.write('IOTCM %s %s Indirect (%s)\nx\n' % (escape(f), _highlight_level, arg))
    interpretResponse(getOutput(), quiet)

def sendCommandLoadHighlightInfo(file: str, quiet: bool):
    sendCommand('Cmd_load_highlighting_info %s' % escape(file), highlight = True, quiet = quiet)

def sendCommandLoad(file: str, quiet: bool):
    if agda.version < AgdaVersion(2,5,0,0): # in 2.5 they changed it so Cmd_load takes commandline arguments
        incpaths = (path.decode('utf-8') for path in vim.vars['agdavim_agda_includepathlist'])
    else:
        incpaths = (x for path in vim.vars['agdavim_agda_includepathlist'] for x in ['-i', path.decode('utf-8')])
    sendCommand('Cmd_load %s %s' % (escape(file), agda2_quote_list(incpaths)), highlight = True, quiet = quiet)

#def getIdentifierAtCursor():
#    (r, c) = vim.current.window.cursor
#    line = vim.current.line
#    try:
#        start = re.search(r"[^\s@(){};]+$", line[:c+1]).start()
#        end = re.search(r"^[^\s@(){};]+", line[c:]).end() + c
#    except AttributeError as e:
#        return None
#    return line[start:end]

def replaceHole(replacement: str):
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


def getHoleBodyAtCursor() -> Optional[Tuple[str, Optional[int]]]:
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


def Agda2HighlightLevel() -> HighlightLevel:
    return HighlightLevel.parse(vim.vars['agdavim_highlight_level'].decode('utf-8'))

## Directly exposed functions: {

@vim_func
def AgdaRestartAgda(path: str):
    '''Tries to start or restart the Agda process.'''
    global agda

    if agda is None:
        logger.info("Starting Agda process with path: %s" % path)
        agda = AgdaProcess(path)
    else:
        logger.info("Restarting Agda process with new path: %s" % path)
        agda.restart(path)


@vim_func(conv={'quiet': vim_bool})
def AgdaHighlightToken(quiet: bool):
    filename = vim.current.buffer.name
    sendCommand('Cmd_tokenHighlighting %s %s' % (escape(filename), HighlightRemove.KEEP), highlight = True, quiet = quiet)


@vim_func
def AgdaQuitAgda():
    '''Quit and clean up after agda2'''
    global agda

    if agda:
        logger.info("Stopping Agda process")
        agda.stop_wait()
        agda = None

@vim_func(conv={'quiet': vim_bool})
def AgdaShowVersion(quiet: bool):
    sendCommand('Cmd_show_version', highlight = False, quiet = quiet)


@vim_func(conv={'quiet': vim_bool})
def AgdaLoad(quiet: bool):
    f = vim.current.buffer.name
    sendCommandLoad(f, quiet)
    if vim.vars['agdavim_enable_goto_definition']:
        sendCommandLoadHighlightInfo(f, quiet)


@vim_func(conv={'quiet': vim_bool})
def AgdaLoadHighlightInfo(quiet: bool):
    f = vim.current.buffer.name
    sendCommandLoadHighlightInfo(f, quiet)


@vim_func
def AgdaGotoAnnotation():
    gotoAnnotation()


@vim_func(conv={'arg': vim_int_range(0,3)})
def AgdaDisplayImplicitArguments(arg: int):
    """Toggle display of implicit arguments.

    Arguments:
        arg: 0 to toggle display of implicit arguments, 1 to turn on, 2 to turn off.
    """
    if arg == 0:
        return sendCommand('ToggleImplicitArgs', highlight = True)
    if arg == 1:
        return sendCommand('ShowImplicitArgs True', highlight = True)
    if arg == 2:
        return sendCommand('ShowImplicitArgs False', highlight = True)


@vim_func(conv={'arg': vim_int_range(0,3)})
def AgdaDisplayIrrelevantArguments(arg: int):
    """Toggle display of irrelevant arguments.

    Arguments:
        arg: 0 to toggle display of irrelevant arguments, 1 to turn on, 2 to turn off.
    """
    if arg == 0:
        return sendCommand('ToggleIrrelevantArgs', highlight = True)
    if arg == 1:
        return sendCommand('ShowIrrelevantArgs True', highlight = True)
    if arg == 2:
        return sendCommand('ShowIrrelevantArgs False', highlight = True)


@vim_func(conv={'useforce': vim_int_range(0,2)})
def AgdaGive(useforce: int):
    if agda.version < AgdaVersion(2,5,3,0):
        useForce = ""
    else:
        useForce = UsePrefixArgs.WITHOUT_FORCE if useforce == 0 else UsePrefixArgs.WITH_FORCE

    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "?":
        sendCommand('Cmd_give %s %d noRange %s' % (useForce, result[1], escape(promptUser("expression to give: "))))
    else:
        sendCommand('Cmd_give %s %d noRange %s' % (useForce, result[1], escape(result[0])))


@vim_func
def AgdaMakeCase():
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "?":
        prompt = "pattern variables to case (empty for split on result): "
        sendCommand('Cmd_make_case %d noRange %s' % (result[1], escape(promptUser(prompt))))
    else:
        sendCommand('Cmd_make_case %d noRange %s' % (result[1], escape(result[0])))


@vim_func(conv={'pmlambda': vim_bool})
def AgdaRefine(pmlambda: bool):
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_refine_or_intro %s %d noRange %s' % (pmlambda, result[1], escape(result[0])))


@vim_func(conv={'quiet': vim_bool})
def AgdaAutoMaybeAll(quiet: bool):
    result = getHoleBodyAtCursor()
    if result is None:
        sendCommand('Cmd_autoAll', highlight = False, quiet = quiet)
    elif result[1] is None:
        print("Goal not loaded")
    else:
        if agda.version < AgdaVersion(2,6,0,0):
            sendCommand('Cmd_auto %d noRange %s' % (result[1], escape(result[0] if result[0] != "?" else "")))
        else:
            sendCommand('Cmd_autoOne %d noRange %s' % (result[1], escape(result[0] if result[0] != "?" else "")))


@vim_func(conv={'normalise': vim_normalise})
def AgdaGoalType(normalise: NormaliseType):
    """Show the type of the goal at point"""
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_goal_type %s %d noRange %s' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaGoalAndContext(normalise: NormaliseType):
    '''Shows the type of the goal at point and the current context'''
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_goal_type_context %s %d noRange %s' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaGoalAndContextAndInferred(normalise: NormaliseType):
    '''Shows the context, the goal and the given expression's inferred type'''
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "":
        prompt = promptUser("expression to type: ")
        sendCommand('Cmd_goal_type_context_infer %s %d noRange %s' % (normalise.name, result[1], escape(prompt)))
    else:
        sendCommand('Cmd_goal_type_context_infer %s %d noRange %s' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaGoalAndContextAndChecked(normalise: NormaliseType):
    '''Shows the context, the goal and check the given expression's against the hole's type'''
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "":
        prompt = promptUser("expression to type: ")
        sendCommand('Cmd_goal_type_context_check %s %d noRange %s' % (normalise.name, result[1], escape(prompt)))
    else:
        sendCommand('Cmd_goal_type_context_check %s %d noRange %s' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaShowContext(normalise: NormaliseType):
    '''Show the context of the goal at point'''
    result = getHoleBodyAtCursor()
    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_context %s %d noRange %s' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaInferTypeMaybeToplevel(normalise: NormaliseType):
    result = getHoleBodyAtCursor()
    if result is None:
        sendCommand('Cmd_infer_toplevel %s %s' % (normalise.name, escape(promptUser("expression to type: "))))
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_infer %s %d noRange %s' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'computeMode': vim_compute_mode})
def AgdaComputeNormalisedMaybeToplevel(computeMode: ComputeMode):
    result = getHoleBodyAtCursor()

    if agda.version < AgdaVersion(2,5,2,0):
        mode = computeMode == ComputeMode.DefaultCompute
        if result is None:
            prompt = promptUser("expression to normalise: ")
            sendCommand('Cmd_compute_toplevel %s %s' % (mode, escape(prompt)))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_compute %s %d noRange %s' % (mode, result[1], escape(result[0])))
    else:
        if result is None:
            prompt = promptUser("expression to normalise: ")
            sendCommand('Cmd_compute_toplevel %s %s' % (computeMode.name, escape(prompt)))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_compute %s %d noRange %s' % (computeMode.name, result[1], escape(result[0])))


@vim_func
def AgdaWhyInScope(termName: str):
    result = getHoleBodyAtCursor() if termName == '' else None

    if result is None:
        termName = getWordAtCursor() if termName == '' else termName
        termName = promptUser("Enter name: ") if termName == '' else termName
        sendCommand('Cmd_why_in_scope_toplevel %s' % escape(termName))
    elif result[1] is None:
        print("Goal not loaded")
    else:
        sendCommand('Cmd_why_in_scope %d noRange %s' % (result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise})
def AgdaSearchAbout(normalise: NormaliseType, name: str = ''):
    '''Search About an identifier.'''
    cname = getWordAtCursor() if name == '' else name
    query = promptUser("Name: ") if cname == '' else cname
    sendCommand('Cmd_search_about_toplevel %s "%s"' % (normalise.name, query))


@vim_func(conv={'normalise': vim_normalise})
def AgdaShowGoals(normalise: NormaliseType):
    sendCommand('Cmd_metas %s' % normalise.name)


@vim_func(conv={'normalise': vim_normalise})
def AgdaModuleContentsMaybeToplevel(normalise: NormaliseType, moduleName: str = ''):
    result = getHoleBodyAtCursor() if moduleName == '' else None

    if agda.version < AgdaVersion(2,4,2,0):
        if result is None:
            moduleName = promptUser("Module name (empty for current module): ") if moduleName == '' else moduleName
            sendCommand('Cmd_show_module_contents_toplevel %s' % escape(moduleName))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_show_module_contents %d noRange %s' % (result[1], escape(result[0])))
    else:
        if result is None:
            moduleName = promptUser("Module name (empty for current module): ") if moduleName == '' else moduleName
            sendCommand('Cmd_show_module_contents_toplevel %s %s' % (normalise.name, escape(moduleName)))
        elif result[1] is None:
            print("Goal not loaded")
        else:
            sendCommand('Cmd_show_module_contents %s %d noRange %s' % (normalise.name, result[1], escape(result[0])))


@vim_func(conv={'normalise': vim_normalise_asis})
def AgdaHelperFunctionType(normalise: NormaliseType):
    result = getHoleBodyAtCursor()

    if result is None:
        print("No hole under the cursor")
    elif result[1] is None:
        print("Goal not loaded")
    elif result[0] == "?":
        sendCommand('Cmd_helper_function %s %d noRange %s' % (normalise.name, result[1], escape(promptUser("Expression: "))))
    else:
        sendCommand('Cmd_helper_function %s %d noRange %s' % (normalise.name, result[1], escape(result[0])))

@vim_func
def AgdaVimSetLoggingLevel(level: int):
    log.set_logging_level(level=level)
    print("Set logging level to %s" % level)


## }
