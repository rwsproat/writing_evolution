#!/bin/bash
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

# Form of the base morph among MONOSYLLABLE, SESQUISYLLABLE, DISYLLABLE
BASE_MORPH=${BASE_MORPH:-MONOSYLLABLE}
# 1 or 0: whether to initialize non primary morphs with the symbol
NON_PRIMARIES=${NON_PRIMARIES:-0}
# Probability to try to spell something
PROB=${PROB:-0.5}
# 1 or 0: Whether to apply ablaut
ABLAUT=${ABLAUT:-0}
# Do not allow any new phonetic symbols after iteration N.
FREEZE_PHONETICS=${FREEZE_PHONETICS:-0}
# Do not allow any semantic spread after iteration N.
FREEZE_SEMANTICS=${FREEZE_SEMANTICS:-0}
#
dir="base_morph_${BASE_MORPH}/prob_${PROB}/non_primaries_${NON_PRIMARIES}/ablaut_${ABLAUT}"
dir="${dir}/freeze_${FREEZE_PHONETICS}"
dir="${dir}/freeze_semantics_${FREEZE_SEMANTICS}"
# Change this directory to the location where the output should be placed
dir=/var/tmp/script_evolution_outputs/${dir}
mkdir -p ${dir}
NITER=${NITER:-10}
# Probably not a good idea to set this much above 2000 otherwise it will be too slow.
NMORPHS=${NMORPHS:-1000}
TIMER=time  # Unset this if you don't want the timer.
# Make this "0 1 2 ..." for as many experiments as you want.
EXPERIMENT_NUMS="0 1 2 3 4"
for expt in ${EXPERIMENT_NUMS}
do
    echo Experiment ${expt}
    mkdir -p ${dir}/${expt}
    ${TIMER} lexicon.py \
	--base_morph=${BASE_MORPH} \
	--probability_to_seek_spelling=${PROB} \
	--initialize_non_primaries_with_symbol=${NON_PRIMARIES} \
	--ablaut=${ABLAUT} \
	--niter=${NITER} \
	--nmorphs=${NMORPHS} \
	--freeze_phonetics_at_iter=${FREEZE_PHONETICS} \
	--freeze_semantics_at_iter=${FREEZE_SEMANTICS} \
	--outdir=${dir}/${expt}
done
