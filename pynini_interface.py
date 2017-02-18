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

import time
import sys

from pynini import *

from base import _BASE

_LOADED_FARS = {}
_LOADED_FSTS = {}


def load_rule_from_far(rule, far, force=False):
  """Loads the rule, and caches it, reloading if force=True

  Args:
    rule: Rule name
    far: Far name
    force: If True, forces reload
  Returns:
    loaded fst or fail if no such fst or far
  """
  try:
    if force or far not in _LOADED_FARS:
      _LOADED_FARS[far] = Far(far)
    # TODO(rws): If there is the same rule name in different fars, then this
    # will just get the first one we encounter.
    if force or rule not in _LOADED_FSTS:
      _LOADED_FSTS[rule] = _LOADED_FARS[far][rule]
    return _LOADED_FSTS[rule]
  except pywrapfst.FstIOError:
    sys.stderr.write('Failed loading far from %s\n' % far)
    sys.exit(1)
  except KeyError:
    sys.stderr.write('No rule "%s" in %s\n' % (rule, far))
    sys.exit(1)


def to_fst(s, syms='byte'):
  """Constructs an fst from a string.

  Args:
    s: string
    syms: symbol table
  Returns:
    fst representing the string
  """
  return acceptor(s, token_type=syms)


def to_string(t):
  """Constructs a string from a fst.

  Args:
    t: fst
  Returns:
    string representing the fst
  """
  t.rmepsilon()
  return t.stringify()


def random_paths(t, n=1):
  """Computes a set of random paths from an fst

  Args:
    t: fst
    n: number of paths 
  Returns:
    list of random path strings
  """
  if type(t) == type('string'):
    try:
      t = _LOADED_FSTS[t]
    except KeyError:
      sys.stderr.write('Missing transducer %s\n' % t)
      return []
  i = 0
  paths = []
  while i < n:
    output = randgen(t, seed=int(time.time() * 1000000), select='uniform')
    output.rmepsilon()
    output.topsort()
    paths.append(output.stringify())
    i += 1
  return paths


_CACHED_COMPOSITIONS = {}


def sounds_like(s1, s2, rule='EDIT_DISTANCE',
                far=('%s/Grm/soundslike.far' % _BASE)):
  """Computes the distance between two phonetic strings given a grammar.

  Args:
    s1: phonetic string 1
    s2: phonetic string 2
    grm: phonetic similarity grammar
  Returns:
    number of arcs in shortest path, shortest distance
  """
  grmfst = load_rule_from_far(rule, far)
  if (s1, rule) in _CACHED_COMPOSITIONS:
    fst1 = _CACHED_COMPOSITIONS[s1, rule]
  else:
    fst1 = s1 * grmfst
    _CACHED_COMPOSITIONS[s1, rule] = fst1
  result = shortestpath(fst1 * s2)
  result.rmepsilon()
  result.topsort()
  if result.num_states() > 1:
    dist = shortestdistance(result)
    dist = (float(str(dist[-1])) +
            float(str(result.final(result.num_states() - 1))))
    return result.num_states() - 1, dist
  else:
    return 0, float('inf')
