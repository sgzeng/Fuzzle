FROM maze-base

# Install dependencies
RUN apt-get update -y && apt-get upgrade -y && apt-get install -y make build-essential

# Install AFL++
RUN git clone https://github.com/aflgo/aflgo.git /home/maze/tools/aflgo
WORKDIR /home/maze/tools/aflgo

RUN /home/maze/tools/aflgo/build.sh

USER maze
RUN sudo chown -R maze:maze /home/maze

ENV AFL_SKIP_CPUFREQ=1
ENV AFL_NO_AFFINITY=1
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1

# Add scripts
ADD visualize_maze_cov.py /home/maze/tools/visualize_maze_cov.py
ADD get_coverage.sh /home/maze/tools/get_coverage.sh
ADD run_aflgo.sh /home/maze/tools/run_aflgo.sh
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py
ADD get_tcs.py /home/maze/tools/get_tcs.py

WORKDIR /home/maze/workspace
