import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / 'hooks' / 'hook.py'
REPO_FILE = '/Users/me/project/src/app.php'
MEMORY_FILE = '/Users/me/.claude/projects/p/memory/note.md'


def user(text):
    return {'type': 'user', 'message': {'role': 'user', 'content': text}}


def tool_result():
    return {'type': 'user', 'message': {'role': 'user', 'content': [{'type': 'tool_result', 'content': 'ok'}]}}


def edit(path=REPO_FILE):
    return {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Edit', 'input': {'file_path': path}}]}}


def bash(command):
    return {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Bash', 'input': {'command': command}}]}}


def say(text):
    return {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': text}]}}


PASS = 'nothing-first: status check in PHP via in_array — the IVR LIMIT 1 picks a closed deal, SQL stays.'


def run_hook(hook_input):
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(hook_input), capture_output=True, text=True, check=True).stdout
    return json.loads(out) if out.strip() else {}


def run_gate(*entries, last_assistant_message=''):
    with tempfile.NamedTemporaryFile('w', suffix='.jsonl', delete=False) as transcript:
        transcript.write('\n'.join(json.dumps(e, ensure_ascii=False) for e in entries))
    hook_input = {'hook_event_name': 'Stop', 'transcript_path': transcript.name, 'last_assistant_message': last_assistant_message}
    return run_hook(hook_input).get('decision')


class SessionStartTest(unittest.TestCase):
    def test_skill_text_is_injected(self):
        context = run_hook({'hook_event_name': 'SessionStart'})['hookSpecificOutput']['additionalContext']
        self.assertIn('The Existence Ladder', context)


class PassGateTest(unittest.TestCase):
    def test_turn_without_edits_stops(self):
        self.assertIsNone(run_gate(user('посмотри'), say('Ответ.')))

    def test_edit_without_pass_is_blocked(self):
        self.assertEqual(run_gate(user('сделай'), edit(), tool_result(), say('Готово.')), 'block')

    def test_edit_followed_by_pass_stops(self):
        self.assertIsNone(run_gate(user('сделай'), edit(), tool_result(), say(PASS)))

    def test_final_message_not_yet_in_transcript_counts(self):
        self.assertIsNone(run_gate(user('сделай'), edit(), tool_result(), last_assistant_message=f'Готово.\n\n{PASS}'))

    def test_improvement_after_pass_needs_another_pass(self):
        self.assertEqual(run_gate(user('сделай'), edit(), tool_result(), say(PASS), edit(), tool_result(), say('Готово.')), 'block')

    def test_second_pass_without_improvement_stops(self):
        self.assertIsNone(run_gate(user('сделай'), edit(), tool_result(), say(PASS), edit(), tool_result(), say(PASS)))

    def test_pass_before_edit_does_not_count(self):
        self.assertEqual(run_gate(user('сделай'), say(PASS), edit(), tool_result(), say('Готово.')), 'block')

    def test_empty_pass_is_blocked(self):
        self.assertEqual(run_gate(user('сделай'), edit(), tool_result(), say('nothing-first: none')), 'block')

    def test_memory_edit_is_not_code(self):
        self.assertIsNone(run_gate(user('запомни'), edit(MEMORY_FILE), tool_result(), say('Запомнил.')))

    def test_bash_in_place_edit_is_blocked(self):
        self.assertEqual(run_gate(user('сделай'), bash(f"sed -i '' 's/a/b/' {REPO_FILE}"), tool_result(), say('Готово.')), 'block')

    def test_bash_scratch_write_is_not_code(self):
        self.assertIsNone(run_gate(user('посчитай'), bash('cd /private/tmp/claude-502/x/scratchpad && cat > a.py <<EOF\nEOF'), tool_result(), say('Итог.')))

    def test_prompt_after_injected_reminder_starts_a_new_turn(self):
        prompt = {'type': 'user', 'message': {'role': 'user', 'content': [
            {'type': 'text', 'text': '<system-reminder>status</system-reminder>'},
            {'type': 'text', 'text': 'смотри каменты'},
        ]}}
        self.assertIsNone(run_gate(user('сделай'), edit(), tool_result(), say('Готово.'), prompt, say('Комментариев нет.')))

    def test_previous_turn_edits_are_ignored(self):
        self.assertIsNone(run_gate(user('сделай'), edit(), tool_result(), say('Готово.'), user('а почему?'), say('Потому что.')))


if __name__ == '__main__':
    unittest.main()
