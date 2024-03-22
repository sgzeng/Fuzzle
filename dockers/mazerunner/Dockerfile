FROM mazerunner
ENV DEBIAN_FRONTEND="noninteractive"

# Install dependencies
RUN apt-get update -y && \
apt-get install -y sudo graphviz libgraphviz-dev \
libfreetype6-dev libqhull-dev libopenblas-dev \
build-essential libfreetype6-dev libqhull-dev pkg-config
WORKDIR /workdir/symsan
RUN git clean -f && git checkout . && git pull
WORKDIR /workdir/symsan/build
RUN make && make install

### Create maze account
SHELL ["/bin/bash", "-c"]
RUN if getent group maze > /dev/null 2>&1; then \
      echo "Group maze already exists"; \
    else \
        groupadd --gid 1000 maze \
        && useradd --uid 1000 --gid maze --shell /bin/bash --create-home maze && \
        echo 'maze  ALL=(root) NOPASSWD: ALL' >> /etc/sudoers; \
    fi
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
WORKDIR /home/maze/workspace
RUN source ~/.bashrc && \
    pyenv global 3.11.5 && \
    pip install --upgrade pip && \
    pip cache purge && \
    pip install pillow matplotlib networkx pygraphviz && \
    pip install -r /workdir/symsan/mazerunner/requirements.txt && \
    pip install z3-solver --force-reinstall --no-cache-dir
RUN echo "3.11.5" > /workdir/symsan/.python-version

# Add scripts
RUN mkdir -p /home/maze/tools
RUN mkdir -p /home/maze/workspace
ADD run_mazerunner-wo-policy.sh /home/maze/tools/run_mazerunner-wo-policy.sh
ADD run_mazerunner-w-policy.sh /home/maze/tools/run_mazerunner-w-policy.sh
ADD utils.py /home/maze/tools/utils.py
ADD monitor.py /home/maze/tools/visualize_maze_cov.py
ADD get_tcs.py /home/maze/tools/get_tcs.py
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py
ADD get_coverage.sh /home/maze/tools/get_coverage.sh

RUN chown -R maze:maze /home/maze
USER root
