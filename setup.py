from distutils.core import setup
from distutils.extension import Extension

from Cython.Build import cythonize
import Cython.Compiler.Options
from cython import __version__ as cython_version

import os
import sys

osx = False
if sys.platform.lower().startswith('darwin'):
    osx = True

extra_compile_args = [
    '-std=c++11',
    '-mfpmath=sse',
    '-msse4.1',
    '-funroll-loops',
    '-ffast-math'
]
include_dirs = [os.path.dirname(os.path.realpath(__file__))]
library_dirs = []

if osx:
    extra_compile_args.extend([
        '-stdlib=libc++',
        '-mmacosx-version-min=10.7',
    ])
else:
    library_dirs.append('rt')


def make_extension(module_name):
    sources = [module_name.replace('.', '/') + '.pyx']
    return Extension(
        module_name,
        sources=sources,
        language="c++",
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        extra_compile_args=extra_compile_args,
        extra_link_args=[])


extensions = cythonize([
    make_extension('xpr.sampler'),
])


setup(version='0.1',
      name='xpr',
      packages=(
          'xpr',
      ),
      ext_modules=extensions)
