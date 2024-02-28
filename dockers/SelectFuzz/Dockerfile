FROM selectfuzz

RUN chmod 1777 /tmp && \
unset https_proxy && \
unset http_proxy && \
git config --global --unset http.proxy && \
git config --global --unset https.proxy

### Prepare apt
RUN sed -i 's/archive.ubuntu.com/ftp.daumkakao.com/g' /etc/apt/sources.list
RUN sed -i 's/# deb-src/deb-src/g' /etc/apt/sources.list
ENV DEBIAN_FRONTEND="noninteractive"

### Create maze account
RUN groupadd --gid 1000 maze \
    && useradd --uid 1000 --gid maze --shell /bin/bash --create-home maze

### Set up directory structure
USER maze
RUN mkdir -p /home/maze/tools
ADD ./utils.py /home/maze/tools/utils.py
RUN mkdir -p /home/maze/workspace

USER root

### Install common packages
RUN apt update && apt upgrade -y
RUN apt install -y vim git wget sudo
RUN echo 'maze  ALL=(root) NOPASSWD: ALL' >> /etc/sudoers
RUN pip3 install matplotlib pillow

USER maze

ENV AFL_SKIP_CPUFREQ=1
ENV AFL_NO_AFFINITY=1
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1

# Add scripts
ADD run_selectfuzz.sh /home/maze/tools/run_selectfuzz.sh
ADD get_tcs.py /home/maze/tools/get_tcs.py
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py
ADD get_coverage.sh /home/maze/tools/get_coverage.sh
RUN wget -P /home/maze/tools/ https://raw.githubusercontent.com/sgzeng/Fuzzle/main/scripts/visualize_maze_cov.py

WORKDIR /home/maze/workspace
