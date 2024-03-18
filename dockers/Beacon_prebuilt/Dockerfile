FROM maze-base

# Install packages needed for Beacon fuzzers
RUN apt-get update -y && apt-get upgrade -y && \
    apt-get install -y make python3 python3-pip file git build-essential bc libncurses5 \
    # For libming
    libfreetype6 libfreetype6-dev

# Setup Beacon
WORKDIR /home/maze/tools
COPY Beacon-binaries/ /home/maze/tools/beacon
COPY ./setup_beacon.sh /home/maze/tools/setup_beacon.sh
RUN ./setup_beacon.sh
RUN pip3 install Pillow

USER maze
RUN sudo chown -R maze:maze /home/maze
ENV CLANGDIR=/home/maze/tools/beacon/llvm4/bin/
ENV WORKDIR=/home/maze/workspace
ENV BEACON=/home/maze/tools/beacon
ENV AFL_SKIP_CPUFREQ=1
ENV AFL_NO_AFFINITY=1
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1

# Add scripts
ADD get_coverage.sh /home/maze/tools/get_coverage.sh
ADD monitor.py /home/maze/tools/visualize_maze_cov.py
ADD run_beacon.sh /home/maze/tools/run_beacon-prebuilt.sh
ADD get_tcs.py /home/maze/tools/get_tcs.py
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py

WORKDIR /home/maze/workspace
