#!/usr/bin/env python3
import io
import os.path
import subprocess
import sys
import tempfile
import textwrap
import unittest


DATA_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), 'data'))


def run_cmd(cmd):
    print("Execute: %s" % ' '.join(cmd))
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except:
        proc.kill()
        proc.wait()
        raise

    exitcode = proc.returncode
    if exitcode:
        sys.exit(exitcode)


class CompareTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cmd = [sys.executable, '-m', 'performance', 'venv', 'create']
        run_cmd(cmd)

    def compare(self, *args, **kw):
        dataset = kw.get('dataset', 'py')
        exitcode = kw.get('exitcode', 0)

        if dataset == 'mem':
            file1 = 'mem1.json'
            file2 = 'mem2.json'
        else:
            file1 = 'py2.json'
            file2 = kw.get('file2', 'py3.json')

        cmd = [sys.executable, '-m', 'performance', 'compare',
               os.path.join(DATA_DIR, file1),
               os.path.join(DATA_DIR, file2)]
        cmd.extend(args)
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)
        stdout = proc.communicate()[0]
        self.assertEqual(proc.returncode, exitcode, repr(stdout))
        return stdout

    def test_compare(self):
        stdout = self.compare()
        self.assertEqual(stdout, textwrap.dedent('''
            py2.json
            ========

            Performance version: 0.2

            py3.json
            ========

            Performance version: 0.2

            ### call_simple ###
            Median +- Std dev: 11.4 ms +- 2.1 ms -> 13.6 ms +- 1.3 ms: 1.19x slower
            Significant (t=-3.38)
        ''').lstrip())

    def test_compare_wrong_version(self):
        stdout = self.compare(file2='py3_performance03.json', exitcode=1)
        self.assertEqual(stdout, textwrap.dedent('''
            py2.json
            ========

            Performance version: 0.2

            py3_performance03.json
            ======================

            Performance version: 0.3

            ### call_simple ###
            Median +- Std dev: 11.4 ms +- 2.1 ms -> 13.6 ms +- 1.3 ms: 1.19x slower
            Significant (t=-3.38)

            ERROR: Performance versions are different: 0.2 != 0.3
        ''').lstrip())

    def test_compare_single_sample(self):
        stdout = self.compare(dataset='mem')
        self.assertEqual(stdout, textwrap.dedent('''
            mem1.json
            =========

            Performance version: 0.2

            mem2.json
            =========

            Performance version: 0.2

            ### call_simple ###
            7896.0 kB -> 7900.0 kB: 1.00x larger
        ''').lstrip())

    def test_csv(self):
        with tempfile.NamedTemporaryFile("w") as tmp:
            self.compare("--csv", tmp.name)

            with io.open(tmp.name, "r") as fp:
                csv = fp.read()

            self.assertEqual(csv, textwrap.dedent('''
                Benchmark,Base,Changed
                call_simple,0.01143,0.01363
            ''').lstrip())

    def test_compare_table(self):
        stdout = self.compare("-O", "table")
        self.assertEqual(stdout, textwrap.dedent('''
            py2.json
            ========

            Performance version: 0.2

            py3.json
            ========

            Performance version: 0.2

            +-------------+----------+----------+--------------+-----------------------+
            | Benchmark   | py2.json | py3.json | Change       | Significance          |
            +=============+==========+==========+==============+=======================+
            | call_simple | 11.4 ms  | 13.6 ms  | 1.19x slower | Significant (t=-3.38) |
            +-------------+----------+----------+--------------+-----------------------+
        ''').lstrip())

    def test_compare_table_single_sample(self):
        stdout = self.compare("-O", "table", dataset='mem')
        self.assertEqual(stdout, textwrap.dedent('''
            mem1.json
            =========

            Performance version: 0.2

            mem2.json
            =========

            Performance version: 0.2

            +-------------+-----------+-----------+--------------+-------------------------------------------+
            | Benchmark   | mem1.json | mem2.json | Change       | Significance                              |
            +=============+===========+===========+==============+===========================================+
            | call_simple | 7896.0 kB | 7900.0 kB | 1.00x larger | (benchmark only contains a single sample) |
            +-------------+-----------+-----------+--------------+-------------------------------------------+
        ''').lstrip())


if __name__ == "__main__":
    unittest.main()
