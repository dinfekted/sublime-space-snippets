import re

def process(begin, end):
  state = _get_state(begin, end)
  if state == None:
    return []

  ignored = ['$', '@', '#', '%', '.', '`', '\\']
  if state['symbols'] in ignored:
    return []

  modifications = []

  _set_new_symbols(state)
  _set_no_spaces(state)
  _process_prefix(state, modifications)
  _process_symbols(state, modifications)
  _process_infix(state, modifications)
  _process_postfix(state, modifications)

  return modifications

def _get_state(begin, end):
  fullline = begin + '~~CURSOR~~' + end

  expr = (
    r'([\(\)\{\}\[\]\.]?)' +
    r'(?<!\s)(\s*)' +
    r'([^\w\$\'\"\`$@#%\.\(\)\{\}\[\]\\]+)' +
    r'(?<!\s)(\s*)'+
    r'([\w\(\)\{\}\[\]]?)~~CURSOR~~' +
    r'(\s*)'
  )

  match = re.search(
    expr,
    fullline
  )

  if match == None:
    return None

  state = {
    'line': fullline,
    'begin': begin,
    'end': end,
    'start': match.start(),
    'starter': match.group(1),
    'starter_len': len(match.group(1)),
    'prefix': match.group(2),
    'prefix_len': len(match.group(2)),
    'symbols': match.group(3),
    'symbols_len': len(match.group(3)),
    'infix': match.group(4),
    'infix_len': len(match.group(4)),
    'char': match.group(5),
    'char_len': len(match.group(5)),
    'postfix': match.group(6),
    'postfix_len': len(match.group(6)),
  }

  return state

def _set_new_symbols(state):
  new_symbols = state['symbols']
  if state['symbols_len'] > 1:
    new_symbols = new_symbols.replace(' ', '')

    table = {
      ':::': ': ::',
      '||!': '|| !',
      '&&!': '&& !',
      '==:': '== :',
    }

    if new_symbols in table:
      new_symbols = table[new_symbols]
    else:
      insert_space = (
        (new_symbols[0] == '=' and new_symbols not in ['==', '===', '=>']) or
        (new_symbols[0] in [')', '}', ']'] and new_symbols[1] != ',') or
        new_symbols[0] == ','
      )

      if insert_space:
        new_symbols = new_symbols[0] + ' ' + new_symbols[1:]
      else:
        prefix = new_symbols[0:2]
        if (prefix == '&&' or prefix == '&&') and len(new_symbols) > 2:
          new_symbols = prefix + ' ' + new_symbols[2:]

  state['new_symbols'] = new_symbols

def _set_no_spaces(state):
  state['no_spaces'] = (
    state['new_symbols'] in ['?', '++', '--', '::', ': ::', '->'] or
    (state['symbols'] == '-' and state['starter'] == '.') or (
      state['symbols'] == '|' and
      re.search(r'{ \|[\s\w,\(\)]+\|$', state['begin']) != None
    )
  )

def _process_prefix(state, modifications):
  if state['start'] == 0:
    return

  no_prefix = (
    state['no_spaces'] or
    state['new_symbols'][0:2] in ['<?'] or
    (state['symbols'] != '|' and state['starter'] in ['(', '[', '{']) or
    (state['symbols'] == '!' and state['char'] in ['(', '[', '{']) or
    state['symbols'][0] == ',' or
    state['new_symbols'] in [':', ';', '//', '/,']
  )

  start = (-state['prefix_len'] - state['symbols_len'] - state['infix_len'] -
    state['char_len'])

  if no_prefix:
    if state['prefix'] != '':
      modifications.append((start, start + state['prefix_len'], ''))
    return

  if state['prefix'] != ' ':
    modifications.append((start, start + state['prefix_len'], ' '))

def _process_symbols(state, modifications):
  if state['new_symbols'] != state['symbols']:
    start = -state['symbols_len'] - state['infix_len'] - state['char_len']
    modifications.append((start, start + state['symbols_len'],
      state['new_symbols']))

def _process_infix(state, modifications):
  no_infix = (
    state['no_spaces'] or
    state['starter'] in ['(', '{', '['] or
    state['new_symbols'] in ['!', '!(', '?(', '<?=', ', :'] or
    (state['symbols_len'] > 1 and (
      state['new_symbols'][0] == ',' or
      state['new_symbols'].endswith(':')
    )) or
    (state['symbols_len'] > 2 and state['new_symbols'].endswith('!')) or (
      state['new_symbols'][0] == '=' and
      state['symbols_len'] != 1 and
      state['new_symbols'][1] != '=' and
      state['new_symbols'][1] != '>'
    )
  )

  start = -state['infix_len'] - state['char_len']

  if no_infix:
    if state['infix'] != '':
      modifications.append((start, start + state['infix_len'], ''))
    return

  if state['infix'] != ' ':
    modifications.append((start, start + state['infix_len'], ' '))

def _process_postfix(state, modifications):
  if state['char'] == '':
    if state['postfix'] != '':
      modifications.append((0, state['postfix_len'], ''))