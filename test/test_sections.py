"""Regression checks for section titles in JATS output."""

import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'convert-to-md.py'
spec = importlib.util.spec_from_file_location('converter', SCRIPT)
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class SectionTitleTests(unittest.TestCase):
    def test_generated_section_has_empty_title(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.md'
            output = Path(directory) / 'output.xml'
            source.write_text('A paragraph without a heading.\n\n# Own heading\n\nMore text.\n',
                              encoding='utf-8')
            self.assertTrue(converter.convert_markdown_to_xml(str(source), str(output)))
            root = ET.parse(output).getroot()

        sections = root.findall('./body/sec')
        self.assertEqual(len(sections), 2)
        self.assertEqual([child.tag for child in sections[0]][:2], ['title', 'p'])
        self.assertEqual(sections[0].find('title').text, None)
        self.assertEqual(sections[1].find('title').text, 'Own heading')

    def test_existing_titles_and_jats_child_order(self):
        xml = ('<article><body>'
               '<sec><title>Existing</title><p>Text</p></sec>'
               '<sec><sec-meta/><label>2</label><fig><caption><title>Figure</title></caption></fig>'
               '<sec><p>Subsection</p></sec></sec>'
               '<sec />'
               '</body></article>')
        result = converter.ensure_section_titles(xml)
        root = ET.fromstring(result)
        sections = root.findall('.//sec')
        self.assertEqual(sections[0].find('title').text, 'Existing')
        self.assertEqual([child.tag for child in sections[1]][:4],
                         ['sec-meta', 'label', 'title', 'fig'])
        self.assertEqual([child.tag for child in sections[2]][:2], ['title', 'p'])
        self.assertEqual([child.tag for child in sections[3]], ['title'])
        self.assertEqual(converter.ensure_section_titles(result), result)


if __name__ == '__main__':
    unittest.main()
