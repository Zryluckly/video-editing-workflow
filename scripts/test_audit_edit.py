"""Behavioral checks for speech-edit structure, not subjective media quality."""
from copy import deepcopy
import unittest
from audit_edit import audit


class EditAuditTests(unittest.TestCase):
    def test_repeat_review_crosses_caption_boundary_without_failing_natural_speech(self):
        cards = [{'fromFrame': 0, 'endFrame': 30, 'text': '我'},
                 {'fromFrame': 30, 'endFrame': 60, 'text': '我周测'}]
        report = audit(self.run, cards, '我我周测', 30)
        hits = [r for r in report['reviewQueue'] if r['kind'] == 'adjacent_text_repeat']
        self.assertTrue(any(r['text'] == '我' and r['firstCard'] == 0 and r['lastCard'] == 1 for r in hits))
        self.assertEqual(report['status'], 'STRUCTURAL_PASS')
        natural = [{'fromFrame': 0, 'endFrame': 60, 'text': '平平无奇，点点关注，400分'}]
        report = audit(self.run, natural, natural[0]['text'], 30)
        self.assertEqual(report['status'], 'STRUCTURAL_PASS')
        self.assertFalse(any(r.get('text', '').isdigit() for r in report['reviewQueue']
                             if r['kind'] == 'adjacent_text_repeat'))

    def setUp(self):
        self.run = [
            {'assetId': 'a', 'sourceStartUs': 0, 'sourceEndUs': 1000000, 'fromFrame': 0, 'endFrame': 30},
            {'assetId': 'a', 'sourceStartUs': 2000000, 'sourceEndUs': 3000000, 'fromFrame': 30, 'endFrame': 60},
        ]
        self.cards = {'cards': [{'fromFrame': 0, 'endFrame': 30, 'text': '数学，英语'},
                                {'fromFrame': 30, 'endFrame': 60, 'text': '回归课本'}]}

    def test_pass_never_claims_listening(self):
        report = audit(self.run, self.cards, '数学英语回归课本', 30)
        self.assertEqual(report['status'], 'STRUCTURAL_PASS')
        self.assertFalse(report['audioVerified'])
        self.assertFalse(report['motionVerified'])
        self.assertFalse(report['actualSilenceMeasured'])

    def test_omit_catches_terminal_punctuation_hidden_by_text_normalization(self):
        punctuated = deepcopy(self.cards)
        punctuated['cards'][0]['text'] = '数学，英语。'
        report = audit(self.run, punctuated, '数学英语回归课本', 30,
                       caption_end_punctuation='omit')
        self.assertTrue(report['captionText']['exactOrderAndMultiplicityMatch'])
        self.assertEqual(report['captionEndPunctuation']['status'], 'OMIT_FAIL')
        self.assertEqual(report['status'], 'STRUCTURAL_FAIL')
        error = next(e for e in report['errors'] if e['kind'] == 'caption_end_punctuation_present')
        self.assertEqual((error['index'], error['punctuation']), (0, '。'))

    def test_numbers_and_in_sentence_punctuation_are_preserved(self):
        run = self.run + [
            {'assetId': 'a', 'sourceStartUs': 4000000, 'sourceEndUs': 5000000,
             'fromFrame': 60, 'endFrame': 90},
        ]
        cards = [
            {'fromFrame': 0, 'endFrame': 30,
             'text': '小数3.14，日期2026.11.07，时间12:30，百分数80%，来自U.K.'},
            {'fromFrame': 30, 'endFrame': 60, 'text': '例如e.g.'},
            {'fromFrame': 60, 'endFrame': 90, 'text': '提及U.S.'},
        ]
        target = ''.join(card['text'] for card in cards)
        report = audit(run, cards, target, 30, caption_end_punctuation='omit')
        self.assertEqual(report['captionEndPunctuation']['status'], 'OMIT_PASS')
        self.assertEqual(report['captionEndPunctuation']['violations'], [])
        abbreviations = [item['abbreviation'] for item in report['captionEndPunctuation']['protectedAbbreviations']]
        self.assertEqual(abbreviations, ['U.K.', 'e.g.', 'U.S.'])

    def test_closing_quotes_and_ascii_closers_cannot_hide_terminal_punctuation(self):
        cards = [
            {'fromFrame': 0, 'endFrame': 30, 'text': '她问：“真的吗？ ”'},
            {'fromFrame': 30, 'endFrame': 60, 'text': '他写下：确定吗？ )]}'},
        ]
        target = ''.join(card['text'] for card in cards)
        report = audit(self.run, cards, target, 30, caption_end_punctuation='omit')
        hits = [e for e in report['errors'] if e['kind'] == 'caption_end_punctuation_present']
        self.assertEqual([(e['punctuation'], e['closingCharacters']) for e in hits],
                         [('？', '”'), ('？', ')]}')])
        self.assertEqual(report['captionEndPunctuation']['status'], 'OMIT_FAIL')

    def test_punctuation_inside_book_title_and_closed_quote_is_reported(self):
        cards = [
            {'fromFrame': 0, 'endFrame': 30, 'text': '我读《故乡。》'},
            {'fromFrame': 30, 'endFrame': 60, 'text': '她说“停！”'},
        ]
        target = ''.join(card['text'] for card in cards)
        report = audit(self.run, cards, target, 30, caption_end_punctuation='omit')
        hits = [e for e in report['errors'] if e['kind'] == 'caption_end_punctuation_present']
        self.assertEqual([(e['punctuation'], e['closingCharacters']) for e in hits],
                         [('。', '》'), ('！', '”')])
        self.assertEqual(report['captionEndPunctuation']['status'], 'OMIT_FAIL')

    def test_literal_punctuation_can_be_allowed_with_a_reported_reason(self):
        cards = [{'fromFrame': 0, 'endFrame': 60, 'text': '展示字符“？”',
                  'captionEndPunctuationExceptionReason': '问号字符用于识别练习'}]
        report = audit(self.run, cards, cards[0]['text'], 30, caption_end_punctuation='omit')
        self.assertEqual(report['status'], 'STRUCTURAL_PASS')
        self.assertEqual(report['captionEndPunctuation']['status'], 'OMIT_PASS')
        self.assertEqual(report['captionEndPunctuation']['exceptions'][0]['reason'],
                         '问号字符用于识别练习')
        self.assertEqual(report['captionEndPunctuation']['violations'], [])

    def test_preserve_and_unset_policies_keep_legacy_structural_behavior(self):
        cards = [{'fromFrame': 0, 'endFrame': 60, 'text': '确定吗？'}]
        baseline = audit(self.run, cards, cards[0]['text'], 30)
        preserved = audit(self.run, cards, cards[0]['text'], 30, caption_end_punctuation='preserve')
        self.assertEqual(baseline['status'], 'STRUCTURAL_PASS')
        self.assertEqual(preserved['status'], 'STRUCTURAL_PASS')
        self.assertEqual(baseline['captionEndPunctuation']['status'], 'NOT_ENABLED')
        self.assertEqual(preserved['captionEndPunctuation']['status'], 'PRESERVE')
        self.assertEqual(baseline['captionText'], preserved['captionText'])
        self.assertEqual(baseline['errors'], preserved['errors'])

    def test_equal_character_count_wrong_order_fails(self):
        wrong = deepcopy(self.cards)
        wrong['cards'][0]['text'] = '英语数学'
        report = audit(self.run, wrong, '数学英语回归课本', 30)
        self.assertEqual(report['status'], 'STRUCTURAL_FAIL')
        self.assertEqual(report['captionText']['actualCharacters'], report['captionText']['targetCharacters'])

    def test_noop_source_shift_is_caught(self):
        shifted = deepcopy(self.run)
        shifted[1]['sourceStartUs'] += 33333
        shifted[1]['sourceEndUs'] += 33333
        report = audit(shifted, self.cards, '数学英语回归课本', 30, baseline_run=self.run)
        self.assertIn('unchanged_run_drift', [e['kind'] for e in report['errors']])

    def test_caption_gap_is_not_silence(self):
        sparse = deepcopy(self.cards)
        sparse['cards'][1]['fromFrame'] = 45
        report = audit(self.run, sparse, '数学英语回归课本', 30)
        self.assertEqual(report['status'], 'STRUCTURAL_PASS')
        self.assertIn('caption_gap_not_audio_silence', [q['kind'] for q in report['reviewQueue']])
        self.assertFalse(report['actualSilenceMeasured'])

    def test_timeline_gap_and_missing_word_fail(self):
        broken = deepcopy(self.run)
        broken[1]['fromFrame'] = 31
        report = audit(broken, self.cards, '数学英语回归课本复盘', 30)
        self.assertIn('timeline_gap_or_overlap', [e['kind'] for e in report['errors']])
        self.assertIn('caption_spoken_text_mismatch', [e['kind'] for e in report['errors']])

    def test_nonadjacent_partial_source_reuse_is_reviewed(self):
        interleaved = [
            {'assetId': 'a', 'sourceStartUs': 0, 'sourceEndUs': 1000000, 'fromFrame': 0, 'endFrame': 30},
            {'assetId': 'b', 'sourceStartUs': 0, 'sourceEndUs': 1000000, 'fromFrame': 30, 'endFrame': 60},
            {'assetId': 'a', 'sourceStartUs': 500000, 'sourceEndUs': 1500000, 'fromFrame': 60, 'endFrame': 90},
        ]
        captions = [{'fromFrame': 0, 'endFrame': 90, 'text': '重复片段需核对'}]
        report = audit(interleaved, captions, '重复片段需核对', 30)
        overlaps = [q for q in report['reviewQueue'] if q['kind'] == 'nonadjacent_partial_source_overlap']
        self.assertEqual(len(overlaps), 1)
        self.assertEqual(overlaps[0]['sourceOverlapEndUs'] - overlaps[0]['sourceOverlapStartUs'], 500000)


if __name__ == '__main__':
    unittest.main()
