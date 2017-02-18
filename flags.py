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

"""Defines poor man's command-line flag parsing.
"""

import getopt
import sys


_FLAGS = []
_DUMMY_STR_FUNCTION_TEMPLATE = """def __x():
  global FLAGS_%s
  FLAGS_%s = "%s"
"""

_DUMMY_NUM_FUNCTION_TEMPLATE = """def __x():
  global FLAGS_%s
  FLAGS_%s = %s
"""


def set_dummy_function_template(option, default_value):
  """Builds the runnable function template.

  Args:
    option: name of flag
    default_value: default value for flag
  Returns:
    Function template to be compiled that sets the variables
  """
  try:
    value = int(default_value)
    return _DUMMY_NUM_FUNCTION_TEMPLATE % (option, option, value)
  except ValueError:
    try:
      value = float(default_value)
      return _DUMMY_NUM_FUNCTION_TEMPLATE % (option, option, value)
    except ValueError:
      return _DUMMY_STR_FUNCTION_TEMPLATE % (option, option, default_value)



def define_flag(option, default_value, documentation):
  """Defines the flag and sets the default value and documentation.

  Args:
    option: name of flag
    default_value: default value for flag
    documentation: documentation string
  Returns:
    None
  """
  _FLAGS.append((option, default_value, documentation))
  function_template = set_dummy_function_template(option, default_value)
  exec(function_template)
  __x()


def usage():
  """Prints usage given the set of supplied flags.

  Returns:
    None
  """
  for option, default_value, documentation in _FLAGS:
    print '\t\t--%s\t"%s" (%s)' % (option, documentation, default_value)


def parse_flags(argv):
  """Parses the flags given the argument list.

  Args:
    argv: argument vector
  Returns:
    None
  """
  try:
    optform= map(lambda x: x[0] + '=', _FLAGS)
    opts, args = getopt.getopt(argv, '', optform)
  except getopt.GetoptError as err:
    print str(err)
    Usage()
    sys.exit(1)
  for opt, arg in opts:
    opt = opt.replace('--', '')
    function_template = set_dummy_function_template(opt, arg)
    exec(function_template)
    __x()
