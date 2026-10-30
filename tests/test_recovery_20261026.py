"""Recovery acceptance: retain archives and add source-accounted editions."""
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '21d9c4db1275ae97e9beee06ea213a6f107d0386'

class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = json.loads(subprocess.check_output(['git', 'show', BASELINE + ':editions.json'], cwd=ROOT, text=True))
        cls.data = json.loads((ROOT / 'editions.json').read_text())
        cls.by_end = {edition['end']: edition for edition in cls.data}

    def test_previous_coverage_is_retained_exactly(self):
        for edition in self.old:
            self.assertEqual(self.by_end[edition['end']], edition)

    def test_two_recovery_editions_account_for_every_issue(self):
        self.assertEqual(self.by_end['2026-10-23']['sourceCount'], 7)
        self.assertEqual(self.by_end['2026-10-30']['sourceCount'], 5)
        self.assertEqual(len(self.by_end['2026-10-23']['cards']), 5)
        self.assertEqual(len(self.by_end['2026-10-30']['cards']), 5)
        self.assertIn('Week-to-date', self.by_end['2026-10-30']['coverage'])
        self.assertIn('October 25', self.by_end['2026-10-30']['coverage'])
        self.assertEqual(sum(e['sourceCount'] for e in self.data), sum(e['sourceCount'] for e in self.old) + 12)

    def test_current_root_and_archive_are_identical(self):
        self.assertEqual(self.data[-1]['end'], '2026-10-30')
        root = (ROOT / 'index.html').read_text()
        archive = (ROOT / 'editions/2026-10-30/index.html').read_text()
        self.assertEqual(root.replace('./styles.css', '../../styles.css').replace('href="./editions/', 'href="../../editions/'), archive)
        self.assertIn('Week-to-date', root)
        self.assertIn('5 developments.', root)

    def test_new_cards_have_clean_matching_issue_links(self):
        permitted = {'https://www.morningbrew.com/issues/' + slug for slug in (
            'dynamic-duo', 'very-vulnerable', 'bumpy-ride', 'a-time-to-give',
            'big-spending', 'basketball-brew', 'pepsi-challenged', 'morning-boo-2026',
            'lifting-the-veil', 'surprising-growth-spurt')}
        for key in ('2026-10-23', '2026-10-30'):
            for card in self.by_end[key]['cards']:
                self.assertIn(card['url'], permitted)
                self.assertTrue(card['title'].strip())
                self.assertLessEqual(len(card['summary'].split()), 75)
                self.assertEqual(card['duration'], 'Read time not supplied')

    def test_public_files_have_no_private_or_tracking_tokens(self):
        paths = [ROOT / 'index.html', ROOT / 'editions.json', *ROOT.glob('editions/*/index.html')]
        for path in paths:
            with self.subTest(path=path):
                self.assertIsNone(re.search(r'@|Label_\d+|mbuuid|mbcid|utm_|/home/|kid=|Armin|Hermes|1a1[0-9a-f]{12,}', path.read_text(), re.I))

if __name__ == '__main__':
    unittest.main()
