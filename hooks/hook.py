import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / 'skills' / 'nothing-first' / 'SKILL.md'
EDIT_TOOLS = {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}
NON_CODE_PATH = re.compile(r'/\.claude/projects/[^/]+/memory/|^/(private/)?tmp/')
BASH_WRITE = re.compile(
    r"\b(sed|perl)\s+-\S*i|\bwrite_text\(|open\([^)]*['\"][wa]['\"]"
    r"|(^|[\s;&|])(>>?|tee(\s+-a)?)\s*[^\s|&;<>]+\.(php|tsx?|m?js|py|sql|json|ya?ml|sh|css|html|vue|go|rb|java|kt|swift|toml|conf|tf|hcl)\b"
)
NON_CODE_COMMAND = re.compile(r'/(private/)?tmp/|/memory/|MEMORY\.md')
PASS_RECORD = re.compile(r'^\s*Simplification:\s*(.{20,})$', re.M)
MISSING_PASS = (
    'nothing-first: code changed in this turn and no simplification pass follows the last change. '
    'Run the pass: build the simplest version that meets every stated requirement and compare. '
    'It wins — apply it and run another pass. It loses — one line '
    '"Simplification: <simpler shape you weighed> — <why it loses>".'
)


def is_user_prompt(entry):
    content = entry.get('message', {}).get('content')
    if isinstance(content, list):
        if any(isinstance(part, dict) and part.get('type') == 'tool_result' for part in content):
            return False
        content = ' '.join(part.get('text', '') for part in content if isinstance(part, dict))
    return isinstance(content, str) and content.strip() != '' and not content.lstrip().startswith('<') and not entry.get('isMeta')


def is_code_edit(tool_use):
    tool_input = tool_use.get('input', {})
    if tool_use.get('name') in EDIT_TOOLS:
        return not NON_CODE_PATH.search(tool_input.get('file_path', '') or tool_input.get('notebook_path', ''))
    if tool_use.get('name') == 'Bash':
        command = tool_input.get('command', '')
        return bool(BASH_WRITE.search(command)) and not NON_CODE_COMMAND.search(command)
    return False


def turns(transcript_path):
    events = []
    for line in open(transcript_path, encoding='utf-8', errors='ignore'):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get('type') == 'user' and is_user_prompt(entry):
            yield events
            events = []
        elif entry.get('type') == 'assistant':
            for part in entry.get('message', {}).get('content') or []:
                if part.get('type') == 'tool_use' and is_code_edit(part):
                    events.append('edit')
                elif part.get('type') == 'text' and PASS_RECORD.search(part.get('text', '')):
                    events.append('pass')
    yield events


def on_session_start(hook_input):
    return {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': SKILL.read_text(encoding='utf-8')}}


def on_stop(hook_input):
    *_, events = turns(hook_input['transcript_path'])
    if events and events[-1] == 'edit' and not PASS_RECORD.search(hook_input.get('last_assistant_message') or ''):
        return {'decision': 'block', 'reason': MISSING_PASS}
    return None


HANDLERS = {'SessionStart': on_session_start, 'Stop': on_stop}

if __name__ == '__main__':
    hook_input = json.load(sys.stdin)
    output = HANDLERS[hook_input['hook_event_name']](hook_input)
    if output:
        print(json.dumps(output, ensure_ascii=False))
