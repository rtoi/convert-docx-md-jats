"""Regression checks for IDs in generated JATS figures and tables."""

import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'convert-to-md.py'
spec = importlib.util.spec_from_file_location('converter', SCRIPT)
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class JatsIdTests(unittest.TestCase):
    def test_conversion_assigns_unique_ids_to_figures_and_tables(self):
        markdown = '''![First figure](one.png)

![Second figure](two.png)

| A | B |
|---|---|
| 1 | 2 |

| C | D |
|---|---|
| 3 | 4 |
'''
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.md'
            output = Path(directory) / 'output.xml'
            source.write_text(markdown, encoding='utf-8')
            self.assertTrue(converter.convert_markdown_to_xml(str(source), str(output)))
            root = ET.parse(output).getroot()

        for name in ('fig', 'table-wrap', 'table'):
            self.assertEqual(len(root.findall(f'.//{name}')), 2)
            self.assertTrue(all(element.get('id') for element in root.findall(f'.//{name}')))

        ids = [element.get('id') for element in root.iter() if element.get('id')]
        self.assertEqual(len(ids), len(set(ids)))

    def test_existing_ids_are_preserved_and_collisions_repaired(self):
        content = ('<article><sec id="fig-fixed"/><fig id="fig-fixed"/>'
                   '<fig id="fig-keep"/><fig id="fig-keep"/>'
                   '<table-wrap id="table-wrap-keep"><table/></table-wrap>'
                   '<table-wrap><table id="table-keep"/></table-wrap></article>')
        result = converter.ensure_figure_and_table_ids(content)
        root = ET.fromstring(result)
        ids = [element.get('id') for element in root.iter() if element.get('id')]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(root.find('sec').get('id'), 'fig-fixed')
        self.assertEqual(root.findall('fig')[1].get('id'), 'fig-keep')
        self.assertEqual(root.findall('table-wrap')[0].get('id'), 'table-wrap-keep')
        self.assertEqual(root.findall('table-wrap')[1].find('table').get('id'), 'table-keep')
        self.assertEqual(converter.ensure_figure_and_table_ids(result), result)


if __name__ == '__main__':
    unittest.main()
