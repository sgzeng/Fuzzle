FROM mazerunner

# Install dependencies
RUN apt-get update -y && apt-get upgrade -y
RUN pip3 install networkx

# Install mazerunner
WORKDIR /home/maze/tools/mazerunner
USER maze
RUN sudo chown -R maze:maze /home/maze

ENV AFL_SKIP_CPUFREQ=1
ENV AFL_NO_AFFINITY=1
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1

ENV PYENV_ROOT="$HOME/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"
ENV PATH="$PYENV_ROOT/shims:$PATH"
RUN eval "$(pyenv init -)"

# Add scripts
ADD visualize_maze_cov.py /home/maze/tools/visualize_maze_cov.py
ADD get_tcs.py /home/maze/tools/get_tcs.py
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py
ADD static_analysis.py /home/maze/tools/static_analysis.py
ADD get_coverage.sh /home/maze/tools/get_coverage.sh
ADD run_mazerunner.sh /home/maze/tools/run_mazerunner.sh

WORKDIR /home/maze/workspace
