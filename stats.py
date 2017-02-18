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

"""Script that computes the basic statistics on the results of a run.

Creates an R script to produce plots in plot.R

Usage: stats.py simulation_output_directory
"""


import glob
import sys

_PLOT = """pdf("plot.pdf")
plot(nsyms, xlab="Epoch", ylab=("Prop"), ylim=c(0, 1),
     type="l", col=1)
par(new=TRUE)
plot(nsemphon, xlab="Epoch", ylab=("Prop"), ylim=c(0, 1),
     type="l", col=2)
par(new=TRUE)
plot(nphon, xlab="Epoch", ylab=("Prop"), ylim=c(0, 1),
     type="l", col=3)
par(new=TRUE)
plot(nsem, xlab="Epoch", ylab=("Prop"), ylim=c(0, 1),
     type="l", col=4)
par(new=TRUE)
plot(nphon + nsemphon, xlab="Epoch", ylab=("Prop"), ylim=c(0, 1),
     type="l", col=5)
legend(1, 0.9,
       col=c(1, 2, 3, 4, 5),
       lty=c(1, 1, 1, 1, 1),
       legend=c("# spellings", "# sem-phon", "# phon", "# sem", "all phon"))
"""


def main(argv):
  print '%10s\t%10s\t%10s\t%10s\t%10s' % ('# morphs',
                                          'prop spell',
                                          'semphon',
                                          'phon',
                                          'sem')
  nsym_list = []
  nsemphon_list = []
  nphon_list = []
  nsem_list = []
  for morph_file in glob.glob(argv[1] + '/morphemes_*.tsv'):
    nsyms = 0
    nsemphon = 0
    nphon = 0
    nsem = 0
    tot = 0.0
    with open(morph_file) as strm:
      for line in strm:
        tot += 1
        if 'NO_SYMBOL' in line:
          continue
        nsyms += 1
        if ':SP>' in line:
          nsemphon +=1
        if ':P>' in line:
          nphon +=1
        if ':S>' in line:
          nsem +=1
    semphon_str = '%d\t%2.2f' % (nsemphon, nsemphon / float(nsyms))
    phon_str = '%d\t%2.2f' % (nphon, nphon / float(nsyms))
    sem_str = '%d\t%2.2f' % (nsem, nsem / float(nsyms))
    print '%10d\t%10f\t%10s\t%10s\t%10s' % (tot, nsyms/tot,
                                            semphon_str, phon_str, sem_str)
    nsym_list.append(str(nsyms/tot))
    nsemphon_list.append(str(nsemphon/tot))
    nphon_list.append(str(nphon/tot))
    nsem_list.append(str(nsem/tot))
  with open('plot.R', 'w') as plot:
    plot.write('nsyms <- c(%s)\n' % ', '.join(nsym_list))
    plot.write('nsemphon <- c(%s)\n' % ', '.join(nsemphon_list))
    plot.write('nphon <- c(%s)\n' % ', '.join(nphon_list))
    plot.write('nsem <- c(%s)\n' % ', '.join(nsem_list))
    plot.write(_PLOT)


if __name__ == '__main__':
  main(sys.argv)
