import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import user_storage as storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.old=self.root/'old exe'
        self.old.mkdir()
        self.new=self.root/'local app data'/'HololiveDreamsHighLowAuto'

    def tearDown(self):
        self.temp.cleanup()

    def test_data_location_is_per_user_and_separate_from_other_games(self):
        with patch.dict(storage.os.environ,LOCALAPPDATA=str(self.root)):
            self.assertEqual(storage.user_data_dir(),self.root/'HololiveDreamsHighLowAuto')

    def test_first_start_moves_exact_records_and_preferences(self):
        records=b'{ "coins":19200,"fails":25,"wins":4,"phased_stage":2,"date":"2026-10-11" }\r\n'
        settings=json.dumps(dict(language='日本語',start_key='Alt+Q',stop_key='INSERT',strategy=1),
                            ensure_ascii=False).encode('utf-8')
        for name,payload in (('daily_coins.json',records),('settings.json',settings)):
            (self.old/name).write_bytes(payload)
        storage.prepare_user_data(self.old,directory=self.new)
        self.assertEqual((self.new/'daily_coins.json').read_bytes(),records)
        self.assertEqual((self.new/'settings.json').read_bytes(),settings)
        self.assertEqual(list(self.old.iterdir()),[])
        self.assertEqual(sorted(p.name for p in self.new.iterdir()),['daily_coins.json','settings.json'])

    def test_existing_appdata_is_never_overwritten_and_old_copy_is_retained(self):
        self.new.mkdir(parents=True)
        (self.new/'daily_coins.json').write_bytes(b'{"coins":12800}')
        (self.old/'daily_coins.json').write_bytes(b'{"coins":19200}')
        storage.prepare_user_data(self.old,directory=self.new)
        self.assertEqual((self.new/'daily_coins.json').read_bytes(),b'{"coins":12800}')
        self.assertEqual((self.old/'daily_coins.json').read_bytes(),b'{"coins":19200}')

    def test_write_failure_leaves_source_intact_and_no_partial_destination(self):
        payload=b'{"coins":19200,"fails":25}'
        (self.old/'daily_coins.json').write_bytes(payload)
        with patch.object(storage.os,'link',side_effect=PermissionError('No write access')):
            with self.assertRaises(PermissionError):
                storage.prepare_user_data(self.old,directory=self.new)
        self.assertEqual((self.old/'daily_coins.json').read_bytes(),payload)
        self.assertEqual(list(self.new.iterdir()),[])

    def test_invalid_ledger_is_not_removed_or_replaced_by_empty_totals(self):
        payload=b'{"coins":'
        (self.old/'daily_coins.json').write_bytes(payload)
        with self.assertRaises(ValueError):
            storage.prepare_user_data(self.old,directory=self.new)
        self.assertEqual((self.old/'daily_coins.json').read_bytes(),payload)
        self.assertEqual(list(self.new.iterdir()),[])

    def test_concurrent_destination_creation_does_not_overwrite_either_record(self):
        original=b'{"coins":19200}'
        other=b'{"coins":400}'
        (self.old/'daily_coins.json').write_bytes(original)
        def publish(_source,target):
            target.write_bytes(other)
            raise FileExistsError()
        with patch.object(storage.os,'link',side_effect=publish):
            storage.prepare_user_data(self.old,directory=self.new)
        self.assertEqual((self.new/'daily_coins.json').read_bytes(),other)
        self.assertEqual((self.old/'daily_coins.json').read_bytes(),original)
        self.assertFalse(list(self.new.glob('*.tmp')))

    def test_old_file_updated_during_copy_is_not_deleted(self):
        (self.old/'daily_coins.json').write_bytes(b'{"coins":19200}')
        link=storage.os.link
        def publish(source,target):
            link(source,target)
            (self.old/'daily_coins.json').write_bytes(b'{"coins":19600}')
        with patch.object(storage.os,'link',side_effect=publish):
            storage.prepare_user_data(self.old,directory=self.new)
        self.assertEqual((self.old/'daily_coins.json').read_bytes(),b'{"coins":19600}')
        self.assertEqual((self.new/'daily_coins.json').read_bytes(),b'{"coins":19200}')

    def test_restart_does_not_create_records_or_leave_temporary_files(self):
        for _ in range(2): storage.prepare_user_data(self.old,directory=self.new)
        self.assertEqual(list(self.new.iterdir()),[])

    def test_corrupt_appdata_stops_migration_without_overwriting_or_removing_old_files(self):
        self.new.mkdir(parents=True)
        (self.new/'daily_coins.json').write_bytes(b'{')
        (self.old/'daily_coins.json').write_bytes(b'{"coins":19200}')
        (self.old/'settings.json').write_bytes(b'{"language":"English"}')
        with self.assertRaises(ValueError):
            storage.prepare_user_data(self.old,directory=self.new)
        self.assertEqual((self.new/'daily_coins.json').read_bytes(),b'{')
        self.assertTrue((self.old/'daily_coins.json').exists())
        self.assertTrue((self.old/'settings.json').exists())
