FROM maze-base

# Install dependencies
RUN apt-get update -y && apt-get install -y \
      wget apt-transport-https git unzip \
      build-essential libtool libtool-bin gdb \
      automake autoconf bison flex python3 sudo vim

# Copied from OSS-FUZZ
ENV OUT=/out
ENV SRC=/src
ENV WORK=/work
ENV PATH="$PATH:/out"
RUN mkdir -p $OUT $SRC $WORK
ENV CMAKE_VERSION 3.21.1
RUN wget https://github.com/Kitware/CMake/releases/download/v$CMAKE_VERSION/cmake-$CMAKE_VERSION-Linux-x86_64.sh && \
    chmod +x cmake-$CMAKE_VERSION-Linux-x86_64.sh && \
    ./cmake-$CMAKE_VERSION-Linux-x86_64.sh --skip-license --prefix="/usr/local" && \
    rm cmake-$CMAKE_VERSION-Linux-x86_64.sh && \
    rm -rf /usr/local/doc/cmake /usr/local/bin/cmake-gui
COPY checkout_build_install_llvm.sh /root/
RUN /root/checkout_build_install_llvm.sh
RUN rm /root/checkout_build_install_llvm.sh

# Install packages needed for fuzzers
RUN apt-get update -y && apt-get install -y \
      # Several packages get uninstalled after LLVM setup.
      git build-essential bc \
      # For libming
      libfreetype6 libfreetype6-dev \
      # For libxml
      python3-dev \
      # For libjpeg
      nasm \
      # For lrzip
      libbz2-dev liblzo2-dev \
      # For 32bit binaries
      gcc-multilib \
      # For DAFL
      libgmp-dev libmpfr-dev pkg-config software-properties-common ca-certificates rsync curl

# Add Scripts
WORKDIR /home/maze
RUN mkdir -p /home/maze/script \
    mkdir -p /home/maze/workspace/src \
    mkdir -p /home/maze/workspace/dafl-input
COPY clang-compile.mk /home/maze/script/clang-compile.mk
COPY dafl-compile.mk /home/maze/script/dafl-compile.mk
COPY dafl-compile-noasan.mk /home/maze/script/dafl-compile-noasan.mk
COPY setup_smake.sh /home/maze/script/setup_smake.sh
# Setup smake.
WORKDIR /home/maze/script
RUN ./setup_smake.sh

# Setup Sparrow
ARG DEBIAN_FRONTEND=noninteractive
ENV NO_ARCH_OPT=1
ENV IS_DOCKER=1
ENV OPAMYES=1
RUN add-apt-repository universe && apt-get update && apt-get install -y libclang-cpp12-dev libclang-12-dev llvm-12-dev libclang-dev llvm-dev ncurses-dev
RUN curl -fsSL -o /usr/local/bin/opam https://github.com/ocaml/opam/releases/download/2.1.5/opam-2.1.5-x86_64-linux && \
    chmod +x /usr/local/bin/opam
COPY setup_Sparrow.sh /home/maze/script/setup_Sparrow.sh
# setup_Sparrow.sh need to run manually
RUN opam init --disable-sandboxing -y && eval $(opam env) && opam option depext=false && /home/maze/script/setup_Sparrow.sh

# Setup DAFL.
RUN mkdir -p /home/maze/fuzzer
WORKDIR /home/maze/fuzzer
COPY setup_DAFL.sh /home/maze/fuzzer/setup_DAFL.sh
RUN ./setup_DAFL.sh

ENV AFL_SKIP_CPUFREQ=1
ENV AFL_TRY_AFFINITY=1
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
USER maze
RUN sudo chown -R maze:maze /home/maze

# Add scripts
ADD visualize_maze_cov.py /home/maze/tools/visualize_maze_cov.py
ADD get_coverage.sh /home/maze/tools/get_coverage.sh
ADD get_tcs.py /home/maze/tools/get_tcs.py
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py
ADD run_dafl.sh /home/maze/tools/run_dafl.sh
WORKDIR /home/maze/workspace
