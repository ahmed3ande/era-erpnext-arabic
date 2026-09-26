"""Regression checks for the site audit without an installed Frappe bench."""

import importlib.util
import io
import sys
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


class SiteAuditTest(unittest.TestCase):
	def setUp(self):
		self.frappe = types.ModuleType("frappe")
		self.frappe.__path__ = []
		self.translate = types.ModuleType("frappe.translate")
		self.translate.get_all_translations = Mock(return_value={"Employee": "الموظف", "API": "API"})
		self.modules = patch.dict(sys.modules, {"frappe": self.frappe, "frappe.translate": self.translate})
		self.modules.start()
		self.addCleanup(self.modules.stop)
		path = Path(__file__).resolve().parents[1] / "arabic_translations/audit.py"
		spec = importlib.util.spec_from_file_location("era_site_audit_under_test", path)
		self.audit = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(self.audit)
		self.harvest = patch.object(self.audit, "_harvest", return_value={
			"Employee": {"Workspace.label"}, "API": {"Report.report_name"},
			"Missing title": {"Dashboard.dashboard_name"},
		})
		self.harvest.start()
		self.addCleanup(self.harvest.stop)

	def test_fresh_process_does_not_require_translate_attribute(self):
		self.assertFalse(hasattr(self.frappe, "translate"))
		with redirect_stdout(io.StringIO()):
			result = self.audit.report(lang="ar-EG")
		self.translate.get_all_translations.assert_called_once_with("ar-EG")
		self.assertEqual(result, {"missing": ["Missing title"], "identical": ["API"]})

	def test_po_output_contains_only_missing_labels(self):
		output = io.StringIO()
		with redirect_stdout(output):
			self.audit.report(as_po=True)
		self.assertIn('msgid "Missing title"', output.getvalue())
		self.assertNotIn('msgid "Employee"', output.getvalue())
		self.assertNotIn('msgid "API"', output.getvalue())

	def test_empty_translation_dictionary(self):
		self.translate.get_all_translations.return_value = None
		with redirect_stdout(io.StringIO()):
			result = self.audit.report()
		self.assertEqual(result["missing"], ["API", "Employee", "Missing title"])
		self.assertEqual(result["identical"], [])
