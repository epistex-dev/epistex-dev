#!/usr/bin/env python3
"""Regression tests for check_readme_steps.py: broken <details> structure must fail. Run: python3 tools/editorial/test_check_readme_steps.py"""
import contextlib, io, os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_readme_steps as c

README = open(os.path.join(c.ROOT, 'README.md')).read()


def run(readme):
    """Runs the checker on a copy of the repo that has `readme` as its README.md; returns (exit code, output)."""
    with tempfile.TemporaryDirectory() as root:
        os.symlink(os.path.join(c.ROOT, 'assets'), os.path.join(root, 'assets'))
        open(os.path.join(root, 'README.md'), 'w').write(readme)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = c.main(root)
    return code, out.getvalue()


class Structure(unittest.TestCase):
    def test_real_readme_passes(self):
        self.assertEqual(run(README)[0], 0)

    def test_missing_close_fails(self):
        code, out = run(README.replace('</details>', '', 1))
        self.assertEqual(code, 1, out)
        self.assertIn('nested', out)

    def test_extra_close_fails(self):
        code, out = run(README.replace('</details>', '</details></details>', 1))
        self.assertEqual(code, 1, out)
        self.assertIn('unmatched', out)

    def test_nested_details_fails(self):
        code, out = run(README.replace('</details>', '<details></details></details>', 1))
        self.assertEqual(code, 1, out)
        self.assertIn('nested', out)


if __name__ == '__main__':
    unittest.main()
