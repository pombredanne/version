#!/usr/bin/env python

import sys, os
import re
import traceback
VERBOSE=False

def version_file(val=None):
	v = "VERSION"
	if os.path.exists(v):
		if val is None:
			with open(v) as f:
				return f.read().strip()
		else:
			with open(v, 'w') as f:
				f.write(val)
			return True
version_file.desc = "VERSION"

def conf_file(val=None):
	return replace("conf.py", re.compile("""(?P<pre>(?:version|release)\s*=\s*['"])(?P<version>[^'"]*)"""), val)
conf_file.desc = "conf.py"

def replace(filename, regex, val):
	if not os.path.exists(filename):
		return None
	with open(filename) as f:
		lines = f.read()
	if val is None:
		return re.search(regex, lines).group('version')
	else:
		with open(filename, 'w') as f:
			f.write(re.sub(regex, r"\g<pre>%s" % (val,), lines))
		return True

def setup_py(val=None):
	return replace("setup.py", re.compile("""(?P<pre>version\s*=\s*['"])(?P<version>[^'"]*)"""), val)
setup_py.desc = "setup.py"

version_strategies = [setup_py, version_file, conf_file]
def version_types(new_version=None):
	def do(strategy):
		try:
			return strategy(new_version)
		except StandardError, e:
			print >> sys.stderr, "[ error: %s  (%s)]" % (e,strategy.desc)
			if VERBOSE:
				traceback.print_exc(file=sys.stderr)
	results = [Version(do(s), desc=s.desc) for s in version_strategies]
	return [r for r in results if r]

class Version(object):
	@classmethod
	def guess(cls):
		version_types()[0]

	def __init__(self, number, desc=None):
		self.number = number
		self.desc = desc
	
	def increment(self, levels=1):
		before, middle, after = split(self.number, levels)
		middle = int(middle) + 1
		after = [0 for part in after]
		all_parts = ".".join(map(str, before + [middle] + after))
		return Version(all_parts)

	def __str__(self):
		return str(self.number)

	def describe(self):
		return "%-8s (%s)" % (self.desc, self.number)

	def __repr__(self):
		return "Version(%r)" % (self.number,)
	
	def __nonzero__(self):
		return self.number is not None

def main(args):
	if len(args) > 1 or '--help' in args:
		print >> sys.stderr, "Usage: %s [version]" % (os.path.basename(sys.argv[0]),)
		sys.exit(1)
	versions = version_types()
	print "\n".join([version.describe() for version in versions])
	if len(args) == 1:
		new_version = get_version(args[0], versions)
		ok = raw_input("\nchange version to %s? " % (new_version.number,)).strip().lower() in ('y','yes','')
		if not ok:
			sys.exit(0)
		changed = version_types(new_version.number)
		print "changed version in %s files." % (len(changed),)

def get_version(input, current_versions):
	"""
	>>> get_version('1234', [])
	Version('1234')
	>>> get_version('+', [Version('0.1.2')])
	Version('0.1.3')
	>>> get_version('+', [Version('0.1.9')])
	Version('0.1.10')
	>>> get_version('+', [Version('0.1')])
	Version('0.2')

	>>> get_version('++', [Version('0.1.2')])
	Version('0.2.0')
	>>> get_version('++', [Version('0.1')])
	Version('1.0')

	"""
	if all([char == '+' for char in input]):
		return current_versions[0].increment(len(input))
	elif input == 'date':
		import time
		v = time.strftime("%Y%m%d.%H%M")
		return Version(v)
	elif input == '=':
		return current_versions[0]
	else:
		return Version(input)

def split(version, idx):
	"""splits a version at idx from the lest-significant portion (starting at 1):

	>>> split('0.1.2', 1)
	(['0', '1'], '2', [])
	>>> split('0.1.2', 2)
	(['0'], '1', ['2'])
	>>> split('0.1.2', 3)
	([], '0', ['1', '2'])

	>>> split('0.1', 1)
	(['0'], '1', [])
	>>> split('0.1', 2)
	([], '0', ['1'])

	>>> split('0.1', 3)
	([], '0', ['1'])
	"""
	parts = version.split(".")
	middle = max(0, len(parts) - idx)
	more_significant = parts[:middle]
	less_significant = parts[middle+1:]
	return (more_significant, parts[middle], less_significant)

if __name__ == '__main__':
	sys_argv = sys.argv[1:]
	argv = [arg for arg in sys_argv if arg not in ('-v',)]
	if '-v' in sys_argv:
		VERBOSE=True
	try:
		main(argv)
	except StandardError, e:
		print >> sys.stderr, e
		if VERBOSE: raise
	except (KeyboardInterrupt, EOFError):
		print ""
