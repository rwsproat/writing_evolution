This is code used in the simulations for the work reported in the forthcoming paper:

Sproat, Richard. 2017. <a href="http://rws.xoba.com/wll.pdf">A Computational Model of the Discovery of
Writing.</a> <em>Written Language and Literacy</em>, to appear.

It depends on the following software:

* OpenFst 1.6.2  -- <a href="http://www.openfst.org">http://www.openfst.org</a>
* Thrax 1.2.3 -- <a
  href="http://www.openfst.org/twiki/bin/view/GRM/Thrax">http://www.openfst.org/twiki/bin/view/GRM/Thrax</a>
* Pynini 1.5 -- <a
  href="http://www.openfst.org/twiki/bin/view/GRM/Pynini">http://www.openfst.org/twiki/bin/view/GRM/Pynini</a>

The main shell script is

<pre>
experiments.sh
</pre>

Run with no environment variables set it will run an experiment with the
following configuration:

<pre>
# Form of the base morph among MONOSYLLABLE, SESQUISYLLABLE, DISYLLABLE
BASE_MORPH=MONOSYLLABLE
# 1 or 0: whether to initialize non primary morphs with the symbol
NON_PRIMARIES=0
# Probability to try to spell something
PROB=0.5
# 1 or 0: Whether to apply ablaut
ABLAUT=0
# Do not allow any new phonetic symbols after iteration N.
FREEZE_PHONETICS=0
# Do not allow any semantic spread after iteration N.
FREEZE_SEMANTICS=0
# Perform NITER iterations per experiment
NITER=10
</pre>

To change one of these, set it as an environment variable. Thus:

<pre>
BASE_MORPH=DISYLLABLE ./experiments.sh
</pre>

The script is set up to run 5 experiments with 10 iterations each. In the first
iteration it builds the Thrax grammars in Grm (if they are not already built from a previous run).

The results of each experiment will be placed in subdirectories of

<pre>/var/tmp/script_evolution_outputs</pre>

A script stats.py is provided to compute statistics over an
experiment. Thus:

<pre>
./stats.py /var/tmp/script_evolution_outputs/base_morph_MONOSYLLABLE/prob_0.5/non_primaries_0/ablaut_0/freeze_0/freeze_semantics_0/0
  # morphs	prop spell	   semphon	      phon	       sem
       864	  0.115741	    0	0.00	    0	0.00	  100	1.00
       864	  0.199074	   35	0.20	   13	0.08	  124	0.72
       864	  0.291667	   71	0.28	   27	0.11	  154	0.61
       864	  0.379630	   99	0.30	   45	0.14	  184	0.56
       864	  0.461806	  126	0.32	   66	0.17	  207	0.52
       864	  0.559028	  160	0.33	   84	0.17	  239	0.49
       864	  0.620370	  175	0.33	  103	0.19	  258	0.48
       864	  0.671296	  190	0.33	  116	0.20	  274	0.47
       864	  0.716435	  201	0.32	  125	0.20	  293	0.47
       864	  0.739583	  209	0.33	  132	0.21	  298	0.47
</pre>

Where "morphs" is the number of morphs, "prop spell" is the proportion of morphs that receive a spelling on a given iteration, "semphon" is the proportion of spellings that are "semantic-phonetic" (i.e. having a graphic expression that encodes both semantic and the phonetic information), "phon" is the proportion that are purely phonetic and "sem" is the proportion that is purely semantic. See the paper for further details.
