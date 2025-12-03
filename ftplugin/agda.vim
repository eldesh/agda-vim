" Only do this when not done yet for this buffer
if exists('b:did_ftplugin')
  finish
endif
let b:did_ftplugin = 1
let b:undo_ftplugin = ''

let s:cpo_save = &cpo
set cpo&vim

" The AgdaReloadSyntax function is reproduced from
" http://wiki.portal.chalmers.se/agda/pmwiki.php?n=Main.VIMEditing
" the remainder is covered by the license described in LICENSE.
function! AgdaReloadSyntax()
    syntax clear
    let f = expand('%:h') . "/." . expand('%:t') . ".vim"
    if filereadable(f)
        exec "source " . escape(f, '*')
    endif
    runtime syntax/agda.vim
endfunction
call AgdaReloadSyntax()

function! AgdaLoad(quiet)
    " Do nothing.  Overidden below with a Python function if python is supported.
endfunction

autocmd QuickfixCmdPost make call AgdaReloadSyntax()|call AgdaShowVersion(v:true)|call AgdaLoad(v:true)

setlocal autowrite
let b:undo_ftplugin .= ' | setlocal autowrite<'

" Path to the Agda executable used by the currently running Agda process.
let s:agdavim_running_agda_path = ''

if !exists('g:agdavim_agda_path') && exists('$AGDAVIM_AGDA_PATH')
    let g:agdavim_agda_path = $AGDAVIM_AGDA_PATH
endif

if !exists('g:agdavim_agda_path')
    let g:agdavim_agda_path = 'agda'
endif

if !exists('g:agdavim_logging_level') && exists('$AGDAVIM_LOGGING_LEVEL')
    let g:agdavim_logging_level = $AGDAVIM_LOGGING_LEVEL
endif

if !exists('g:agdavim_logging_level')
    let g:agdavim_logging_level = 'WARNING'
endif

let g:agdavim_agda_includepathlist = deepcopy(['.'] + get(g:, 'agda_extraincpaths', []))
call map(g:agdavim_agda_includepathlist, ' ''"'' . v:val . ''"'' ')
let &l:makeprg = 'agda --vim ' . '-i ' . join(g:agdavim_agda_includepathlist, ' -i ') . ' %'
let b:undo_ftplugin .= ' | setlocal makeprg<'

if get(g:, 'agdavim_includeutf8_mappings', v:true)
    runtime agda-utf8.vim
endif

let g:agdavim_enable_goto_definition = get(g:, 'agdavim_enable_goto_definition', v:true) ? v:true : v:false

setlocal errorformat=\ \ /%\\&%f:%l\\,%c-%.%#,%E/%\\&%f:%l\\,%c-%.%#,%Z,%C%m,%-G%.%#
let b:undo_ftplugin .= ' | setlocal errorformat<'

setlocal nolisp
let b:undo_ftplugin .= ' | setlocal nolisp<'

setlocal formatoptions-=t
setlocal formatoptions+=croql
let b:undo_ftplugin .= ' | setlocal formatoptions<'

setlocal autoindent
let b:undo_ftplugin .= ' | setlocal autoindent<'

" {-
" -- Foo
" -- bar
" -}
setlocal comments=sfl:{-,mb1:--,ex:-},:--
let b:undo_ftplugin .= ' | setlocal comments<'

setlocal commentstring=--\ %s
let b:undo_ftplugin .= ' | setlocal commentstring<'

setlocal iskeyword=@,!-~,^\,,^\(,^\),^\",^\',192-255
let b:undo_ftplugin .= ' | setlocal iskeyword<'

setlocal matchpairs&vim
setlocal matchpairs+=(:)
setlocal matchpairs+=<:>
setlocal matchpairs+=[:]
setlocal matchpairs+={:}
setlocal matchpairs+=«:»
setlocal matchpairs+=‹:›
setlocal matchpairs+=⁅:⁆
setlocal matchpairs+=⁽:⁾
setlocal matchpairs+=₍:₎
setlocal matchpairs+=⌈:⌉
setlocal matchpairs+=⌊:⌋
setlocal matchpairs+=〈:〉
setlocal matchpairs+=⎛:⎞
setlocal matchpairs+=⎝:⎠
setlocal matchpairs+=⎡:⎤
setlocal matchpairs+=⎣:⎦
setlocal matchpairs+=⎧:⎫
setlocal matchpairs+=⎨:⎬
setlocal matchpairs+=⎩:⎭
setlocal matchpairs+=⎴:⎵
setlocal matchpairs+=❨:❩
setlocal matchpairs+=❪:❫
setlocal matchpairs+=❬:❭
setlocal matchpairs+=❮:❯
setlocal matchpairs+=❰:❱
setlocal matchpairs+=❲:❳
setlocal matchpairs+=❴:❵
setlocal matchpairs+=⟅:⟆
setlocal matchpairs+=⟦:⟧
setlocal matchpairs+=⟨:⟩
setlocal matchpairs+=⟪:⟫
setlocal matchpairs+=⦃:⦄
setlocal matchpairs+=⦅:⦆
setlocal matchpairs+=⦇:⦈
setlocal matchpairs+=⦉:⦊
setlocal matchpairs+=⦋:⦌
setlocal matchpairs+=⦍:⦎
setlocal matchpairs+=⦏:⦐
setlocal matchpairs+=⦑:⦒
setlocal matchpairs+=⦓:⦔
setlocal matchpairs+=⦕:⦖
setlocal matchpairs+=⦗:⦘
setlocal matchpairs+=⸠:⸡
setlocal matchpairs+=⸢:⸣
setlocal matchpairs+=⸤:⸥
setlocal matchpairs+=⸦:⸧
setlocal matchpairs+=⸨:⸩
setlocal matchpairs+=〈:〉
setlocal matchpairs+=《:》
setlocal matchpairs+=「:」
setlocal matchpairs+=『:』
setlocal matchpairs+=【:】
setlocal matchpairs+=〔:〕
setlocal matchpairs+=〖:〗
setlocal matchpairs+=〘:〙
setlocal matchpairs+=〚:〛
setlocal matchpairs+=︗:︘
setlocal matchpairs+=︵:︶
setlocal matchpairs+=︷:︸
setlocal matchpairs+=︹:︺
setlocal matchpairs+=︻:︼
setlocal matchpairs+=︽:︾
setlocal matchpairs+=︿:﹀
setlocal matchpairs+=﹁:﹂
setlocal matchpairs+=﹃:﹄
setlocal matchpairs+=﹇:﹈
setlocal matchpairs+=﹙:﹚
setlocal matchpairs+=﹛:﹜
setlocal matchpairs+=﹝:﹞
setlocal matchpairs+=（:）
setlocal matchpairs+=＜:＞
setlocal matchpairs+=［:］
setlocal matchpairs+=｛:｝
setlocal matchpairs+=｟:｠
setlocal matchpairs+=｢:｣
let b:undo_ftplugin .= ' | setlocal matchpairs<'

" Python 3 is NOT supported.  This code and other changes are left here to
" ease adding future Python 3 support.  Right now the main issue is that
" Python 3 treats strings are sequences of characters rather than sequences of
" bytes which interacts poorly with the fact that the column offsets vim
" returns are byte offsets in the current line.  The code below should run
" under Python 3, but it won't match up the holes correctly if you have
" Unicode characters.
function! s:UsingPython2()
  if has('python3')
    return 0
  endif
  return 1
endfunction

let s:using_python2 = s:UsingPython2()
let s:python_cmd = s:using_python2 ? 'py ' : 'py3 '
let s:python_loadfile = s:using_python2 ? 'pyfile ' : 'py3file '
let s:python_eval = s:using_python2 ? 'pyeval' : 'py3eval'

if has('python') || has('python3')

function! s:LogAgda(name, text, append)
    let agdawinnr = bufwinnr('__Agda__')
    let prevwinnr = winnr()
    if agdawinnr == -1
        let eventignore_save = &eventignore
        set eventignore=all

        silent keepalt botright 8split __Agda__

        let &eventignore = eventignore_save
        setlocal noreadonly
        setlocal buftype=nofile
        setlocal bufhidden=hide
        setlocal noswapfile
        setlocal nobuflisted
        setlocal nolist
        setlocal nonumber
        setlocal nowrap
        setlocal textwidth=0
        setlocal nocursorline
        setlocal nocursorcolumn

        if exists('+relativenumber')
            setlocal norelativenumber
        endif
    else
        let eventignore_save = &eventignore
        set eventignore=BufEnter

        execute agdawinnr . 'wincmd w'
        let &eventignore = eventignore_save
    endif

    let lazyredraw_save = &lazyredraw
    set lazyredraw
    let eventignore_save = &eventignore
    set eventignore=all

    let &l:statusline = a:name
    if a:append == v:true
        silent put =a:text
    else
        silent %delete _
        silent 0put =a:text
    endif

    0

    let &lazyredraw = lazyredraw_save
    let &eventignore = eventignore_save

    let eventignore_save = &eventignore
    set eventignore=BufEnter

    execute prevwinnr . 'wincmd w'
    let &eventignore = eventignore_save
endfunction

" Show the path of the running (or configured) Agda executable.
function! AgdaShowRunningPath()
    call s:LogAgda('Agda path', 'Running Agda executable: ' . s:agdavim_running_agda_path, v:false)
endfunction

function! AgdaRestart(agda_path)
    if a:agda_path !=# ''
        let g:agdavim_agda_path = a:agda_path
    endif
    if s:agdavim_running_agda_path ==# g:agdavim_agda_path
        call s:LogAgda('Agda restart', 'Agda is already running: ' . g:agdavim_agda_path, v:false)
        return
    endif
    call AgdaRestartAgda(g:agdavim_agda_path)
    if s:agdavim_running_agda_path !=# ''
        call s:LogAgda('Agda restart', 'Restarting Agda executable: ' . g:agdavim_agda_path, v:false)
    endif
    let s:agdavim_running_agda_path = g:agdavim_agda_path
endfunction

execute s:python_cmd . ' ' . 'import agdavim'

command! -buffer -nargs=0 AgdaLoad call AgdaLoad(v:false)
command! -buffer -nargs=0 AgdaShowVersion call AgdaShowVersion(v:false)
command! -buffer -nargs=0 AgdaReload silent! make!|redraw!
command! -buffer -nargs=0 AgdaShowRunningPath call AgdaShowRunningPath()
command! -buffer -nargs=? AgdaDisplayImplicitArguments call AgdaDisplayImplicitArguments(<f-args>)
command! -buffer -nargs=0 AgdaToggleImplicitArguments call AgdaDisplayImplicitArguments(0)
command! -buffer -nargs=0 AgdaShowImplicitArguments call AgdaDisplayImplicitArguments(1)
command! -buffer -nargs=0 AgdaHideImplicitArguments call AgdaDisplayImplicitArguments(2)
command! -buffer -nargs=0 AgdaConstraints exec s:python_cmd "sendCommand('Cmd_constraints')"
command! -buffer -nargs=1 AgdaShowGoals call AgdaShowGoals(<f-args>)
command! -buffer -nargs=0 AgdaSolveAll exec s:python_cmd "sendCommand('Cmd_solveAll')"
command! -buffer -nargs=+ AgdaModuleContentsMaybeToplevel call AgdaModuleContentsMaybeToplevel(<f-args>)
command! -buffer -nargs=1 AgdaWhyInScope call AgdaWhyInScope(<args>)
command! -buffer -nargs=0 AgdaQuitAgda call AgdaQuitAgda() | let s:agdavim_running_agda_path = ''
command! -buffer -nargs=+ AgdaSearchAbout call AgdaSearchAbout(<f-args>)

command! -buffer -nargs=? AgdaVimSetLoggingLevel
    \ if <q-args> !=# '' |
    \   let g:agdavim_logging_level = <q-args> |
    \ endif |
    \ call AgdaVimSetLoggingLevel(g:agdavim_logging_level)

command! -buffer -nargs=? -complete=file AgdaRestart
    \ if <q-args> !=# '' |
    \   let g:agdavim_agda_path = <q-args> |
    \ endif |
    \ call AgdaRestart(g:agdavim_agda_path)

nnoremap <buffer> <LocalLeader>l :<C-u>AgdaReload<CR>
nnoremap <buffer> <LocalLeader>t :<C-u>call AgdaInferTypeMaybeToplevel(v:count)<CR>
nnoremap <buffer> <LocalLeader>r :<C-u>call AgdaRefine(v:false)<CR>
nnoremap <buffer> <LocalLeader>R :<C-u>call AgdaRefine(v:true)<CR>
nnoremap <buffer> <LocalLeader>g :<C-u>call AgdaGive()<CR>
nnoremap <buffer> <LocalLeader>c :<C-u>call AgdaMakeCase()<CR>
nnoremap <buffer> <LocalLeader>a :<C-u>call AgdaAuto()<CR>
nnoremap <buffer> <LocalLeader>e :<C-u>call AgdaShowContext(v:count)<CR>
nnoremap <buffer> <LocalLeader>, :<C-u>call AgdaGoalAndContext(v:count)<CR>
nnoremap <buffer> <LocalLeader>. :<C-u>call AgdaGoalAndContextAndInferred(v:count)<CR>
nnoremap <buffer> <LocalLeader>; :<C-u>call AgdaGoalAndContextAndChecked(v:count)<CR>
nnoremap <buffer> <LocalLeader>n :<C-u>call AgdaComputeNormalisedMaybeToplevel(v:count)<CR>
nnoremap <buffer> <LocalLeader>o :<C-u>call AgdaModuleContentsMaybeToplevel(v:count)<CR>
nnoremap <buffer> <LocalLeader>y :<C-u>call AgdaWhyInScope('')<CR>
nnoremap <buffer> <LocalLeader>h :<C-u>call AgdaHelperFunctionType(v:count)<CR>
nnoremap <buffer> <LocalLeader>d :<C-u>call AgdaGotoAnnotation()<CR>
nnoremap <buffer> <LocalLeader>m :<C-u>call AgdaShowGoals(v:count)<CR>
nnoremap <buffer> <LocalLeader>z :<C-u>call AgdaSearchAbout(v:count)<CR>
nnoremap <buffer> <LocalLeader>xh :<C-u>call AgdaDisplayImplicitArguments(v:count)<CR>
nnoremap <buffer> <LocalLeader>xr :<C-u>AgdaRestart<CR>
nnoremap <buffer> <LocalLeader>xq :<C-u>AgdaQuitAgda<CR>

" Show/reload goals
nnoremap <buffer> <C-e> :<C-u>call AgdaShowGoals(v:count)<CR>
inoremap <buffer> <C-e> <C-o>:<C-u>call AgdaShowGoals(v:count)<CR>

" Go to next/previous goal
nnoremap <buffer> <silent> <C-g>  :let _s=@/<CR>/ {!\\| ?<CR>:let @/=_s<CR>2l
inoremap <buffer> <silent> <C-g>  <C-o>:let _s=@/<CR><C-o>/ {!\\| ?<CR><C-o>:let @/=_s<CR><C-o>2l

nnoremap <buffer> <silent> <C-y>  2h:let _s=@/<CR>? {!\\| \?<CR>:let @/=_s<CR>2l
inoremap <buffer> <silent> <C-y>  <C-o>2h<C-o>:let _s=@/<CR><C-o>? {!\\| \?<CR><C-o>:let @/=_s<CR><C-o>2l

AgdaReload
AgdaVimSetLoggingLevel
AgdaRestart

endif

let &cpo = s:cpo_save
