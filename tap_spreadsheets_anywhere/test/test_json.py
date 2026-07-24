import unittest

import dateutil
from io import StringIO
from tap_spreadsheets_anywhere import configuration, file_utils, csv_handler, json_handler
from tap_spreadsheets_anywhere.format_handler import get_row_iterator

TEST_TABLE_SPEC = {
    "tables": [
        {
            "path": "file://./tap_spreadsheets_anywhere/test",
            "name": "list",
            "pattern": ".*\\.json",
            "start_date": "2017-05-01T00:00:00Z",
            "key_properties": [],
            "format": "json"
        },
        {
            "path": "file://./tap_spreadsheets_anywhere/test",
            "name": "nestedlist",
            "pattern": ".*\\.json",
            "start_date": "2017-05-01T00:00:00Z",
            "key_properties": [],
            "json_path": "someKey",
            "format": "json"
        },
        {
            "path": "file://./tap_spreadsheets_anywhere/test",
            "name": "deepnestedlist",
            "pattern": ".*\\.json",
            "start_date": "2017-05-01T00:00:00Z",
            "key_properties": [],
            "json_path": "response.data[*]",
            "format": "json"
        }
    ]
}

# Table spec pointing at the empty.json fixture (0-byte file downloaded from S3)
EMPTY_FILE_TABLE_SPEC = {
    "path": "file://./tap_spreadsheets_anywhere/test",
    "name": "empty_contact_events",
    "pattern": "empty\\.json",
    "start_date": "2017-05-01T00:00:00Z",
    "key_properties": [],
    "format": "json"
}


class TestFormatHandler(unittest.TestCase):

    def test_json_flat_array(self):
        reader = StringIO('[{"k":"v"},{"k":"v"},{"k":"v"}]')
        json_handler.get_row_iterator(TEST_TABLE_SPEC['tables'][0], reader)

    def test_json_object_lists(self):
        reader = StringIO('{"k":"v"}\n{"k":"v"}\n{"k":"v"}')
        json_handler.get_row_iterator(TEST_TABLE_SPEC['tables'][0], reader)

    def test_json_nested_array(self):
        reader = StringIO('{"someKey": [{"k":"v"},{"k":"v"},{"k":"v"}]}')
        iterator = json_handler.get_row_iterator(TEST_TABLE_SPEC['tables'][1], reader)
        for row in iterator:
            self.assertEqual(row['k'], 'v')

    def test_json_deep_nested_array(self):
        reader = StringIO('{"response": {"data": [{"k":"v"},{"k":"v"},{"k":"v"}]}}')
        iterator = json_handler.get_row_iterator(TEST_TABLE_SPEC['tables'][2], reader)
        for row in iterator:
            self.assertEqual(row['k'], 'v')

    def test_json_empty_file(self):
        """Empty files (0 bytes) should yield zero records, not raise an exception."""
        reader = StringIO('')
        iterator = json_handler.get_row_iterator(TEST_TABLE_SPEC['tables'][0], reader)
        rows = list(iterator)
        self.assertEqual(rows, [])

    def test_json_whitespace_only_file(self):
        """Files containing only whitespace should yield zero records, not raise an exception."""
        reader = StringIO('   \n  \n  ')
        iterator = json_handler.get_row_iterator(TEST_TABLE_SPEC['tables'][0], reader)
        rows = list(iterator)
        self.assertEqual(rows, [])

    def test_empty_json_fixture_via_format_handler(self):
        """Uses the real 0-byte fixture file (sourced from S3 MDM export) via get_row_iterator."""
        uri = './tap_spreadsheets_anywhere/test/empty.json'
        iterator = get_row_iterator(EMPTY_FILE_TABLE_SPEC, uri)
        rows = list(iterator)
        self.assertEqual(rows, [])

    def test_empty_json_fixture_via_write_file(self):
        """Uses the real 0-byte fixture file through the full write_file stack."""
        import json as json_mod
        from unittest.mock import patch

        with patch('singer.write_record') as mock_write:
            schema = {"properties": {}}
            records_synced = file_utils.write_file('empty.json', EMPTY_FILE_TABLE_SPEC, schema)
        self.assertEqual(records_synced, 0)
        mock_write.assert_not_called()
