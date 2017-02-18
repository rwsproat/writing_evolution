## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Author: Richard Sproat (rws@xoba.com)

"""Builds all the needed grammars and lists, placing them in Data directory.
"""

import os
import sys

import pynini_interface

from base import _BASE

_VOWELS = set()


# TODO(rws): Remove dependency on Thrax entirely by rewriting the grammars in
# Pynini.
def build_grammar(name):
  """Builds the grammars using Thrax, and extracts the relevant fsts.

  This assumes that thrax utility thraxmakedep is accessible.

  Args:
    name: name for the grammar.
  Returns:
    None
  """
  os.system('thraxmakedep %s/Grm/%s.grm' % (_BASE, name))
  os.system('make')
  os.system('rm -f Makefile')
  load_vowel_definitions()


def load_vowel_definitions():
  """Loads the vowel definitions from phonemes.tsv.

  Returns:
    None
  """
  with open('%s/Grm/phonemes.tsv' % _BASE) as stream:
    for line in stream:
      try:
        clas, segment = line.split()
      except ValueError:
        continue
      if clas.startswith('V'): 
        _VOWELS.add(segment)


def is_vowel(segment):
  """Returns true if segment is a vowel.

  Args:
    segment: name of the segmeent
  Returns:
    Boolean
  """
  return segment in _VOWELS


def build_morphology_grammar():
  """Builds the morphology grammar.

  Returns:
    None
  """
  build_grammar('morphology')


def build_soundslike_grammar():
  """Builds the sounds-like grammar.

  Returns:
    None
  """
  build_grammar('soundslike')  


def generate_morphs(base_morph='MONOSYLLABLE', n=1000,
                    far=("%s/Grm/morphology.far" % _BASE)):
  """Generates a set of morphs according to the base_morph template.

  Args:
    base_morph: name of the base morph rule, e.g. MONOSYLLABLE
    n: number of morphs to generate
  Returns:
    list of morphs
  """
  pynini_interface.load_rule_from_far(base_morph, far)
  return pynini_interface.random_paths(base_morph, n)


def dump_morphs(morphs, outfile=None):
  """Dumps the morphs to a file.

  Args:
    morphs: list of morphs
    outfile: output file, or stdout if None
  Returns:
    None
  """
  stream = sys.stdout
  if outfile:
    stream = open(outfile, 'w')
  for morph in morphs:
    stream.write(morph + '\n')
  if outfile:
    stream.close()


def apply_ablaut(morphs):
  """Applies the ablaut rule to a set of morphs.

  Args:
    morphs: list of morphs
  Returns:
    ablauted list of morphs
  """
  ablaut_rule = pynini_interface.load_rule_from_far(
    'ABLAUT',
    '%s/Grm/morphology.far' % _BASE)
  ablauted = []
  for morph in morphs:
    morph_fst = pynini_interface.to_fst(morph)
    result = pynini_interface.shortestpath(morph_fst * ablaut_rule)
    result.project(True)
    result = pynini_interface.to_string(result)
    # We do not allow it to delete the morph entirely.
    if result:
      ablauted.append(result)
    else:
      ablauted.append(morph)
  return ablauted
