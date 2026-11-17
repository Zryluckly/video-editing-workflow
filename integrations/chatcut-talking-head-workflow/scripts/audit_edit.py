"""Compatibility entrypoint; implementation lives in video-editing-workflow."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

_target = Path(__file__).resolve().parents[3] / 'scripts' / 'audit_edit.py'
_spec = spec_from_file_location('_video_editing_audit', _target)
if _spec is None or _spec.loader is None:
    raise ImportError(f'Cannot load canonical audit: {_target}')
_module = module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
normalize = _module.normalize
frame = _module.frame
audit = _module.audit
read_json = _module.read_json
main = _module.main

if __name__ == '__main__':
    raise SystemExit(main())
