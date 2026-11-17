"""Compatibility test entrypoint; tests live in video-editing-workflow."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import unittest

_target = Path(__file__).resolve().parents[3] / 'scripts' / 'test_audit_edit.py'
_spec = spec_from_file_location('_video_editing_audit_tests', _target)
if _spec is None or _spec.loader is None:
    raise ImportError(f'Cannot load canonical tests: {_target}')
_module = module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
EditAuditTests = _module.EditAuditTests

if __name__ == '__main__':
    unittest.main()
