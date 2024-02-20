FROM mazerunner

# Install dependencies
RUN apt update && apt -y upgrade && apt -y install make build-essential
RUN pip install nbformat nbconvert

# Install mazerunner
WORKDIR /home/maze/tools/aflgo

# TODO: patch AFLGo
# ADD aflgo.patch /home/maze/tools/aflgo.patch
# RUN patch -p1 < ../aflgo.patch

USER maze

ENV AFL_SKIP_CPUFREQ=1
ENV AFL_NO_AFFINITY=1
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
export PATH="$PYENV_ROOT/shims:$PATH"
eval "$(pyenv init -)"

# Add scripts
ADD run_mazerunner.py /home/maze/tools/run_mazerunner.py
ADD get_tcs.py /home/maze/tools/get_tcs.py
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py
ADD get_coverage.sh /home/maze/tools/get_coverage.sh

WORKDIR /home/maze/workspace
