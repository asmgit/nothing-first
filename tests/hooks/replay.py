import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'hooks'))
from hook import turns

edit_turns = [events for transcript in (Path.home() / '.claude' / 'projects').glob('*/*.jsonl') for events in turns(transcript) if 'edit' in events]
print(f'turns with code edits: {len(edit_turns)}, ended with a simplification pass: {sum(events[-1] == "pass" for events in edit_turns)}')
