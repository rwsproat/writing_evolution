#!/usr/bin/env python
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

"""Defines the lexicon, morphemes, and concepts associated with morphemes.
"""

# NB: "semantics" and "concept" are used interchangeably

# TODO(rws): This seems to generate rather too many morphemes
# associated with a particular concept (e.g. 36 for TEMPLE).

# TODO(rws): Correct class method names to lower case standard.

import builder
import concepts
import flags
import log
import os
import random
import re
import sys
import time

from pynini_interface import sounds_like

# Maximum distance that a closest pronunciation can have
_MAX_DISTANCE = 0.6
# Probability of reusing an existing spelling
# TODO(rws): Make this a paremeter
_PROBABILITY_TO_REUSE_SPELLING = 0.01
# Markup colors
_BLUE = '\033[34m%s\033[0m'
_RED = '\033[31m%s\033[0m'


def _clean_colors(string):
  """Helper to clean up shell color markers from string.

  Args:
    string: string with possible color markers
  Returns:
    cleaned string
  """
  string = string.replace('\033[34m', '')
  string = string.replace('\033[31m', '')
  string = string.replace('\033[0m', '')
  return string


def _phonetic_color(string):
  """Adds color for phonetic graphemes to string.

  Args:
    string: string with symbols
  Returns:
    string with phonetic marker (_RED)
  """
  return _RED % (_clean_colors(string))


def _semantic_color(string):
  """Adds color for semantic graphemes to string.

  Args:
    string: string with symbols
  Returns:
    string with semantic marker (_BLUE)
  """
  return _BLUE % (_clean_colors(string))


def _uniqify_symbol_list(symbols):
  """Removes duplicate symbols from list.

  Args:
    symbols: list of symbols
  Returns:
    uniquified list
  """
  seen = set()
  new_symbols = []
  for symbol in symbols:
    if symbol.name not in seen:
      new_symbols.append(symbol)
      seen.add(symbol.name)
  return new_symbols


def _clean_name(name):
  """Cleans up symbol name of bracketings for presentation.

  Args:
    name: symbol name
  Returns:
    cleaned name
  """
  name = re.sub(r'\[[A-Za-z0-9\.]+\]', '', name)
  name = re.sub(r'\([A-Za-z0-9\.]+\)', '', name)
  name = name.replace('{', '').replace('}', '')
  return name


# BEGIN: class Lexicon
class Lexicon(object):
  """Holder for morphemes.
  """
  def __init__(self):
    """Sets up tables to allow lookup of morphemes by sound or meaning.

    semantics_to_morphemes_primary indicates which morpheme is
    considered the primary exponent of a concept.
    """
    self._phonology_to_morphemes = {}
    self._semantics_to_morphemes = {}
    self._semantics_to_morphemes_primary = {}
    self._used_spellings = set()
    self._used_pron_spellings = set()
    self._used_sem_spellings = set()
    self._morphemes = []
    self._matrix = {}  # Distance matrix to be used by PhonologicalDistance
    self._phonetics_frozen = False
    self._semantics_frozen = False

  def add_morpheme(self, morpheme):
    """Adds a morpheme to the lexicon.

    Args:
      morpheme: a Morpheme instance
    Returns:
      None
    """
    phonology = morpheme.phonology
    semantics = morpheme.semantics
    spelling = morpheme.symbol
    if phonology in self._phonology_to_morphemes:
      self._phonology_to_morphemes[phonology].append(morpheme)
    else:
      self._phonology_to_morphemes[phonology] = [morpheme]
    if semantics.name in self._semantics_to_morphemes:
      self._semantics_to_morphemes[semantics.name].append(morpheme)
    else:
      self._semantics_to_morphemes[semantics.name] = [morpheme]
    if morpheme.is_primary:
      self._semantics_to_morphemes_primary[semantics.name] = morpheme
    if spelling:
      str_spelling = str(spelling)
      self._used_spellings.add(str_spelling)
    self._morphemes.append(morpheme)

  def find_morphemes(self, key):
    """Finds morphemes by sound or meaning.

    Args:
     key: key to search in phonology or semantics tables
    Returns:
     morphemes related to key
    """
    try:
      return self._phonology_to_morphemes[key]
    except KeyError:
      pass
    try:
      return self._semantics_to_morphemes[key]
    except KeyError:
      return []

  def apply_ablaut(self):
    """Applies an ablauting operation to all of the morphs.

    This results in multiple phonological forms being associated with the same
    morpheme.

    Returns:
      None
    """
    keys = self._phonology_to_morphemes.keys()
    ablauted = builder.apply_ablaut(keys)
    i = 0
    while i < len(keys):
      phonology = ablauted[i]
      for morpheme in self._phonology_to_morphemes[keys[i]]:
        # We have already ablauted this morpheme
        if morpheme.marked: continue
        morpheme.add_alternative_phonology(phonology)
        morpheme.mark()
        if phonology in self._phonology_to_morphemes:
          if morpheme not in self._phonology_to_morphemes[phonology]:
            self._phonology_to_morphemes[phonology].append(morpheme)
        else:
          self._phonology_to_morphemes[phonology] = [morpheme]
      i += 1
    # Finally unmark all the morphemes
    for key in self._phonology_to_morphemes:
      for morpheme in self._phonology_to_morphemes[key]:
        morpheme.unmark()

  def dump_morphemes(self, outfile = None):
    """Writes out morphemes to a file, or to stdout.

    Args:
      outfile: An output file, or stdout if None
    Returns:
      None
    """
    stream = sys.stdout
    if outfile:
      stream = open(outfile, 'w')
    for key in self._phonology_to_morphemes:
      for morpheme in self._phonology_to_morphemes[key]:
        stream.write('%s\t%s\t%s\n' % (key, morpheme.symbol_name(), morpheme))
    if outfile:
      stream.close()

  def pronunciations(self):
    """Returns all pronunciations.
    """
    return self._phonology_to_morphemes.keys()

  def useful_pronunciations(self):
    """Returns useful pronunciations: those associated with written symbols.
    """
    prons = []
    for pron in self._phonology_to_morphemes:
      for morpheme in self._phonology_to_morphemes[pron]:
        if not morpheme.symbol: continue
        prons.append(pron)
        break
    return prons

  def dump_morphs(self, outfile = None):
    """Writes out morphs to a file, or to stdout.

    Args:
      outfile: An output file, or stdout if None
    Returns:
      None
    """
    stream = sys.stdout
    if outfile:
      stream = open(outfile, 'w')
    for key in self._phonology_to_morphemes:
      stream.write('%s\n' % key)
    if outfile:
      stream.close()

  def used_spellings(self):
    """Returns list of spellings that are already used.
    """
    return list(self._used_spellings)

  def get_symbols_from_pron(self, pron):
    """Finds and returns all symbols associated with this pronunciation.

    Converts these to phonological components.
    """
    if pron not in self._phonology_to_morphemes: return []
    result = []
    for morpheme in self._phonology_to_morphemes[pron]:
      if morpheme.symbol:
        symbol = Symbol(morpheme.symbol.name, pron)
        if (self._phonetics_frozen and
            str(symbol) not in self._used_pron_spellings):
          log.log('Disallowing use of {} as phonetic'.format(str(symbol)))
          continue
        symbol._colored_name = _phonetic_color(morpheme.symbol.colored_name)
        result.append(symbol)
    return _uniqify_symbol_list(result)

  def get_symbols_from_sem(self, sem):
    """Finds and returns all symbols associated with this meaning.
    """
    if sem not in self._semantics_to_morphemes: return []
    result = []
    for morpheme in self._semantics_to_morphemes[sem]:
      if morpheme.symbol:
        symbol = Symbol(morpheme.symbol.name, sem)
        if (self._semantics_frozen and
            str(symbol) not in self._used_sem_spellings):
          log.log('Disallowing use of {} as semantic'.format(str(symbol)))
          continue
        symbol._colored_name = _semantic_color(morpheme.symbol.colored_name)
        # TODO(rws): This needs to be reworked since we don't necessarily "use"
        # this below, so it could be returned to be recycled.
        self._used_sem_spellings.add(str(symbol))
        result.append(symbol)
    return _uniqify_symbol_list(result)

  def generate_new_spellings(self):
    """Generates new spellings with some probability for each morpheme.

    Works on morphemes that have no spelling. UsefulPronunciations are
    updated to PhonologicalDistance once each cycle.

    Returns:
      None
    """
    useful_pronunciations = self.useful_pronunciations()
    log.log('# of useful pronunciations = %d' % len(useful_pronunciations))
    distance = PhonologicalDistance(useful_pronunciations, self._matrix)
    morphemes_without_symbols = []
    for morpheme in self._morphemes:
      if not morpheme.symbol:
        morphemes_without_symbols.append(morpheme)
    log.log('# of morphemes without symbols = %d' %
            len(morphemes_without_symbols))
    init_time = time.clock()
    for morpheme in morphemes_without_symbols:
      init_time = time.clock()
      if random.random() < flags.FLAGS_probability_to_seek_spelling:
        ## TODO(rws): at some point we should add in the alternative phonology
        ## for ablauted forms, otherwise those will never participate: actually
        ## not completely true since the ablauted forms do inherit from the base
        ## form so that an ablauted form "work" might be spelled based on the
        ## phonology of the base form "werk"
        pron = morpheme.phonology
        if pron == '': continue  # Shouldn't happen
        close_prons = distance.closest_prons(pron)
        phonological_spellings = []
        spelling_to_pron = {}  # Stores pron associated w/ each new spelling
        for close_pron, unused_cost in close_prons:
          prons = close_pron.split('.')
          if len(prons) == 1:  # A single pronunciation
            spellings = self.get_symbols_from_pron(prons[0])
            for spelling in spellings:
              spelling_to_pron[spelling.name] = close_pron
            phonological_spellings += spellings
          elif len(prons) == 2:  # A telescoped pronunciation
            phonological_spellings1 = self.get_symbols_from_pron(prons[0])
            phonological_spellings2 = self.get_symbols_from_pron(prons[1])
            for p1 in phonological_spellings1:
              for p2 in phonological_spellings2:
                spelling = p1 + p2
                spelling.set_denotation(close_pron)
                phonological_spellings.append(spelling)
                spelling_to_pron[spelling.name] = close_pron
        concept = morpheme.semantics
        semantic_spellings = []
        for sem in concept.name.split(','):
          semantic_spellings += self.get_symbols_from_sem(sem)
        # Also tries the whole composite concept:
        if ',' in concept.name:
          semantic_spellings += self.get_symbols_from_sem(concept.name)
        new_spellings = phonological_spellings + semantic_spellings
        log_string = '\n>>>>>>>>>>>>>>>>>>>>>>>>>\n'
        log_string += 'For morpheme: %s, %s:\n' % (concept, pron)
        log_string += 'Phonetic spellings:\n'
        for phonological_spelling in phonological_spellings:
          log_string += '%s\n' % phonological_spelling
        log_string += 'Semantic spellings:\n'
        for semantic_spelling in semantic_spellings:
          log_string += '%s\n' % semantic_spelling
        log_string += '<<<<<<<<<<<<<<<<<<<<<<<<<'
        log.log(log_string)
        for phonological_spelling in phonological_spellings:
          for semantic_spelling in semantic_spellings:
            combo_spelling = semantic_spelling + phonological_spelling
            combo_spelling.set_denotation(semantic_spelling.denotation + '+' +
                                          phonological_spelling.denotation)
            spelling_to_pron[
              combo_spelling.name] = spelling_to_pron[phonological_spelling.name]
            new_spellings.append(combo_spelling)
        # TODO(rws): this is an experiment. Note that with this setting,
        # eliminating the ridiculously long spellings then picking randomly from
        # among these, gets a proportion of semantic/phonetic spellings of 0.32
        # for the MONOSYLLABLE setting.
        tmp = []
        for sp in new_spellings:
          if len(sp) < 5: tmp.append(sp)
        new_spellings = tmp
        random.shuffle(new_spellings)
        # Whereas with this setting, commented out for now, always favoring the
        # absolute shortest, semphon is much lower for 1000, though if you
        # increase to 5000 it gets to around 0.22. Presumably that is because
        # with the larger vocab one starts to actually need the semphon
        # spellings:
        #
        # new_spellings.sort(lambda x, y: cmp(len(x), len(y)))
        for spelling in new_spellings:
          reuse = str(spelling) in self._used_spellings
          if (not reuse or random.random() < _PROBABILITY_TO_REUSE_SPELLING):
            pron = ''
            if spelling.name in spelling_to_pron:
              pron = spelling_to_pron[spelling.name]
            morpheme.set_spelling(spelling)
            self._used_spellings.add(str(spelling))
            log_string = 'Spelling: %s\t' % spelling
            log_string += 'Morpheme: %s\t' % str(morpheme)
            if pron:
              self._used_pron_spellings.add(str(spelling))
              log_string += 'Source-pronunciation: %s\t' % pron
            if reuse:
              log_string += 'Reuse'
            log.log(log_string)
            break

  def log_pron_to_symbol_map(self):
    """Adds pron/symbol mapping for the (usually final) lexicon.

    Returns:
      None
    """
    for pron in self._phonology_to_morphemes:
      for morpheme in self._phonology_to_morphemes[pron]:
        if morpheme.symbol:
          log.log('SYMBOL:\t{}\t{}'.format(morpheme.symbol, pron))

  def freeze_phonetics(self):
    """Freezes the phonetics.
    """
    self._phonetics_frozen = True

  def freeze_semantics(self):
    """Freezes the semantics.
    """
    self._semantics_frozen = True
# END: class Lexicon


# BEGIN: class Morpheme
class Morpheme(object):
  """Container for a morpheme object consisting of sound paired with meaning.
  """

  def __init__(self, phonology, semantics, symbol, is_primary):
    self._phonology = phonology
    self._alternative_phonology = []  # For ablauted forms, etc
    self._semantics = semantics
    self._symbol = symbol
    # set representation of semantics
    self._semantics_set = set(semantics.name.split(','))
    self._is_primary = is_primary  # Is the primary exponent of this concept
    # Book-keeping placeholder to mark whether an operation has applied:
    self._marked = False  

  def __repr__(self):
    alternative_phonology = ''
    if self._alternative_phonology:
      alternative_phonology = '(%s)' % ','.join(self._alternative_phonology)
    symbol = ''
    if self._symbol:
      symbol = '<%s:%s:%s>' % (str(self._symbol),
                               self._symbol.symbols(),
                               self._symbol.type())
    props = '{%s%s:%s:%s:%d}' % (self._phonology,
                                 alternative_phonology,
                                 str(self._semantics).replace('@', ''),
                                 symbol,
                                 self._is_primary)
    return props

  @property
  def phonology(self):
    return self._phonology

  @property
  def semantics(self):
    return self._semantics

  @property
  def is_primary(self):
    return self._is_primary

  @property
  def marked(self):
    return self._marked

  @property
  def symbol(self):
    return self._symbol

  def symbol_name(self):
    if self._symbol:
      return self._symbol.colored_name
    else:
      return '<NO_SYMBOL>'

  def mark(self):
    self._marked = True

  def unmark(self):
    self._marked = False

  def has_semantics(self, semantics):
    return semantics in self._semantics_set

  def add_alternative_phonology(self, phonology):
    if phonology not in self._alternative_phonology:
      self._alternative_phonology.append(phonology)

  def set_spelling(self, spelling):
    self._symbol = spelling
# END: class Morpheme

# BEGIN: class Concept
class Concept(object):
  """A representation of meaning.
  """
  def __init__(self, name):
    """name is a comma-separated set of primitives.
    """
    self._name = name

  def __repr__(self):
    return self._name

  @property
  def name(self):
    return self._name
# END: class Concept

# BEGIN: class Symbol
class Symbol(object):
  """Representation for a symbol and what kind of thing it represents.

  name is a string of one or more symbols
  """
  def __init__(self, name, denotation=None):
    """Denotation type defaults to semantic
    """
    self._name = name
    self._denotation = denotation
    # _colored_name is the symbol's spelling marked with red or blue according
    # to whether it is being used as phonetic or semantic.
    if not denotation or denotation.startswith('@'):
      self._colored_name = _BLUE % name
    else:
      self._colored_name = _RED % name

  def __repr__(self):
    if self._denotation.startswith('@'):
      denotation = '[%s]' % self._denotation[1:]
    else:
      denotation = '(%s)' % self._denotation
    return '{%s}%s' % (self._name, denotation)

  def __add__(self, other):
    new_symbol = Symbol(str(self) + str(other))
    new_symbol._colored_name = self.colored_name + other.colored_name
    return new_symbol

  def __len__(self):
    """Length is the number of basic symbols comprising this.
    """
    length = 0
    for c in unicode(str(self), 'utf8'):
      if ord(c) > 128:
        length += 1
    return length

  @property
  def name(self):
    return self._name

  @property
  def denotation(self):
    return self._denotation

  @property
  def colored_name(self):
    return self._colored_name

  def set_denotation(self, denotation):
    self._denotation = denotation

  def type(self):
    """Classification as S(emantic), P(honetic), or SP.
    """
    if '+' in self._denotation: return 'SP'
    if self._denotation.startswith('@'): return 'S'
    return 'P'

  def symbols(self):
    """Returns string of just the symbols.
    """
    return_value = ''
    for c in unicode(str(self), 'utf8'):
      if ord(c) > 128:
        return_value += c
    return return_value.encode('utf8')
# END: class Symbol

# BEGIN: class LexiconGenerator
class LexiconGenerator(object):
  """Generator for lexicon with specified number of morphs and base morph type.
  """
  def __init__(self, nmorphs = 5000, base_morph = 'MONOSYLLABLE'):
    self._nmorphs = nmorphs
    self._base_morph = base_morph
    self._initial = True

  def select_morphs(self, morphs):
    """Helper function to select from 1 to 3 morphs from a sequence.

    Args:
      morphs: list of morphs
    Returns:
      random selection among the morphs
    """
    selections = set()
    num_selections = random.choice([1, 2, 3])
    i = 0
    while i < num_selections:
      morph = random.choice(morphs)
      selections.add(morph)
      i += 1
    return selections

  def concept_combinations(self, concepts):
    """Randomly generates a set of one to three concepts.

    Args:
      concepts: list of concepts
    Returns:
      random selection among the concepts
    """
    num_concepts = random.choice([1, 2, 3])
    return ','.join(random.sample(concepts, num_concepts))

  def generate(self, force = False):
    """Generates and returns a lexicon.

    Args:
      force: if True then force building of the grammars.
    Returns:
      a Lexicon
    """
    if self._initial or force:
      builder.build_morphology_grammar()
      builder.build_soundslike_grammar()
    morphs = builder.generate_morphs(self._base_morph, self._nmorphs)
    nth_concept = 0
    # Gets the concepts
    concepts_ = concepts.CONCEPTS
    lexicon = Lexicon()
    seen_morphs = set()
    for concept in concepts_.keys():
      selections = self.select_morphs(morphs)
      is_primary = True
      for morph in selections:
        seen_morphs.add(morph)
        # As this has a basic concept, assign the symbol associated with this
        # concept as the symbol.
        # TODO(rws): make it a parameter whether the non-primaries get the
        # symbol.
        my_symbol = None
        if is_primary or flags.FLAGS_initialize_non_primaries_with_symbol:
          my_symbol = Symbol(concepts_[concept], concept)
        lexicon.add_morpheme(Morpheme(morph,
                                      Concept(concept),
                                      my_symbol,
                                      is_primary))
        is_primary = False
    # After that the next sets of morphemes are assigned to random combinations
    # of concepts, one per morph.
    combinations = set()
    for morph in morphs:
      if morph in seen_morphs: continue
      concept = self.concept_combinations(concepts_.keys())
      lexicon.add_morpheme(Morpheme(morph,
                                    Concept(concept),
                                    None,
                                    False if concept in combinations else True))
      combinations.add(concept)
    return lexicon
# END: class LexiconGenerator

# BEGIN: class PhonologicalDistance
class PhonologicalDistance(object):
  """Computes the phonological distance for a set of terms
  """
  def __init__(self, pronunciations, matrix = {}):
    self._pronunciations = pronunciations
    self._matrix = matrix
    self._telescopings = {}
    self.compute_cross_product()

  def __memoize__(self, pron1, pron2):
    """Memoizes the distance for a particular pair of prons for efficiency.

    Args:
      pron1: first pronunciation
      pron2: second pronunciation
    Returns:
      the sounds_like distance between the prons
    """
    if pron1 == pron2: return 0
    if (pron1, pron2) in self._matrix:
      return self._matrix[pron1, pron2]
    length, cost = sounds_like(pron1, pron2)
    try:
      weighted_cost = cost / length
    except ZeroDivisionError:
      weighted_cost = float('Infinity')
    self._matrix[pron1, pron2] = weighted_cost
    return self._matrix[pron1, pron2]

  def compute_cross_product(self):
    """Finds all pairs p1, p2, where p1 ends in a V and p2 starts with a V.

    Returns:
      None
    """
    pairs = []
    for p1 in self._pronunciations:
      if not builder.is_vowel(p1[-1]): continue
      for p2 in self._pronunciations:
        if p1[-1] == p2[0]:
          new_pron = p1 + p2[1:]
          if new_pron not in self._pronunciations:
            # The only way to get this new pronunciation is via telescoping
            # so in that case only we add this to the set of new pairs
            pair = p1 + '.' + p2
            # Note that this may be ambiguous: this just gets the last pair
            # that could produce this pronunciation.
            self._telescopings[new_pron] = pair
            pairs.append(new_pron)
    self._pronunciations += pairs

  def expand(self, pron):
    """Possibly expand into a pair of telescoped elements

    Args:
      pron
    Returns:
      telescoping of pron if in _telescopings, else pron
    """
    if pron in self._telescopings:
      return self._telescopings[pron]
    return pron

  def closest_prons(self, pron1):
    """Returns an ordered list of closest prons to pron.
    """
    result = []
    for pron2 in self._pronunciations:
      result.append((self.expand(pron2), self.__memoize__(pron1, pron2)))
    result.sort(lambda x, y: cmp(x[1], y[1]))
    return [x for x in result if x[1] <= _MAX_DISTANCE]
# END: class PhonologicalDistance


def main(argv):
  global _PROBABILITY_TO_SEEK_SPELLING
  flags.define_flag('ablaut',
                    '0',
                    'Apply ablaut')
  flags.define_flag('base_morph',
                    'MONOSYLLABLE',
                    'Base morpheme shape to use')
  flags.define_flag('initialize_non_primaries_with_symbol',
                    '0',
                    'Sets whether or not non primary morphs get the '
                    'symbol initially')
  flags.define_flag('niter',
                    '5',
                    'Number of iterations')
  flags.define_flag('nmorphs',
                    '1000',
                    'Number of morphs')
  flags.define_flag('outdir',
                    '/var/tmp/simulation',
                    'Output directory')
  # Probability that one will seek a spelling for a morpheme
  # TODO(rws): make this sensitive to lexical frequency
  flags.define_flag('probability_to_seek_spelling',
                    '0.3',
                    'Probability to seek spelling for a form')
  flags.define_flag('freeze_phonetics_at_iter',
                    '0',
                    'Do not allow any new phonetic symbols after iteration N')
  flags.define_flag('freeze_semantics_at_iter',
                    '0',
                    'Do not allow any new semantic spread after iteration N')
  flags.parse_flags(argv[1:])
  generator = LexiconGenerator(nmorphs=flags.FLAGS_nmorphs,
                               base_morph=flags.FLAGS_base_morph)
  lexicon = generator.generate()
  print '{} {}'.format('Probability to seek spelling is',
                        flags.FLAGS_probability_to_seek_spelling)
  print 'Base morph is', flags.FLAGS_base_morph
  print '{} {}'.format('initialize_non_primaries_with_symbol is',
                        flags.FLAGS_initialize_non_primaries_with_symbol)
  print 'Apply ablaut =', flags.FLAGS_ablaut
  print 'outdir =', flags.FLAGS_outdir
  print 'niter =', flags.FLAGS_niter
  print 'nmorphs =', flags.FLAGS_nmorphs
  if flags.FLAGS_ablaut:
    lexicon.apply_ablaut()
  outdir = flags.FLAGS_outdir
  try:
    os.makedirs(outdir)
  except OSError:
    pass
  lexicon.dump_morphemes(outdir + '/morphemes_0000.tsv')
  with open(outdir + '/log.txt', 'w') as stream:
    log.LOG_STREAM = stream
    for i in range(1, flags.FLAGS_niter):
      if flags.FLAGS_freeze_phonetics_at_iter == i:
        lexicon.freeze_phonetics()
      if flags.FLAGS_freeze_semantics_at_iter == i:
        lexicon.freeze_semantics()
      print 'Iteration %d' % i
      log.log('Iteration %d' % i)
      lexicon.generate_new_spellings()
      lexicon.dump_morphemes(outdir + '/morphemes_%04d.tsv' % i)
    lexicon.log_pron_to_symbol_map()
  

if __name__ == '__main__':
  main(sys.argv)
  
