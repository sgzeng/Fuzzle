FROM maze-base

### Comment out to enable these features
# Only available on specific ARM64 boards
ENV NO_CORESIGHT=1
# Possible but unlikely in a docker container
ENV NO_NYX=1

### Only change these if you know what you are doing:
# Current recommended LLVM version is 16
ENV LLVM_VERSION=16
# GCC 12 is producing compile errors for some targets so we stay at GCC 11
ENV GCC_VERSION=11

### No changes beyond the point unless you know what you are doing :)

ARG DEBIAN_FRONTEND=noninteractive

ENV NO_ARCH_OPT=1
ENV IS_DOCKER=1

RUN apt-get update && apt-get full-upgrade -y && \
    apt-get install -y --no-install-recommends wget ca-certificates apt-utils && \
    rm -rf /var/lib/apt/lists/*

RUN echo "deb [signed-by=/etc/apt/keyrings/llvm-snapshot.gpg.key] http://apt.llvm.org/jammy/ llvm-toolchain-jammy-${LLVM_VERSION} main" > /etc/apt/sources.list.d/llvm.list && \
    wget -qO /etc/apt/keyrings/llvm-snapshot.gpg.key https://apt.llvm.org/llvm-snapshot.gpg.key

RUN apt-get update && \
    apt-get -y install --no-install-recommends \
    make cmake automake meson ninja-build bison flex \
    git xz-utils bzip2 wget jupp nano bash-completion less vim joe ssh psmisc \
    python3 python3-dev python3-pip python-is-python3 \
    libtool libtool-bin libglib2.0-dev \
    apt-transport-https gnupg dialog \
    gnuplot-nox libpixman-1-dev bc \
    gcc-${GCC_VERSION} g++-${GCC_VERSION} gcc-${GCC_VERSION}-plugin-dev gdb lcov \
    clang-${LLVM_VERSION} clang-tools-${LLVM_VERSION} libc++1-${LLVM_VERSION} \
    libc++-${LLVM_VERSION}-dev libc++abi1-${LLVM_VERSION} libc++abi-${LLVM_VERSION}-dev \
    libclang1-${LLVM_VERSION} libclang-${LLVM_VERSION}-dev \
    libclang-common-${LLVM_VERSION}-dev libclang-rt-${LLVM_VERSION}-dev libclang-cpp${LLVM_VERSION} \
    libclang-cpp${LLVM_VERSION}-dev liblld-${LLVM_VERSION} \
    liblld-${LLVM_VERSION}-dev liblldb-${LLVM_VERSION} liblldb-${LLVM_VERSION}-dev \
    libllvm${LLVM_VERSION} libomp-${LLVM_VERSION}-dev libomp5-${LLVM_VERSION} \
    lld-${LLVM_VERSION} lldb-${LLVM_VERSION} llvm-${LLVM_VERSION} \
    llvm-${LLVM_VERSION}-dev llvm-${LLVM_VERSION}-runtime llvm-${LLVM_VERSION}-tools \
    $([ "$(dpkg --print-architecture)" = "amd64" ] && echo gcc-${GCC_VERSION}-multilib gcc-multilib) \
    $([ "$(dpkg --print-architecture)" = "arm64" ] && echo libcapstone-dev) && \
    rm -rf /var/lib/apt/lists/*
    # gcc-multilib is only used for -m32 support on x86
    # libcapstone-dev is used for coresight_mode on arm64

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-${GCC_VERSION} 0 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-${GCC_VERSION} 0 && \
    update-alternatives --install /usr/bin/clang clang /usr/bin/clang-${LLVM_VERSION} 0 && \
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-${LLVM_VERSION} 0

RUN wget -qO- https://sh.rustup.rs | CARGO_HOME=/etc/cargo sh -s -- -y -q --no-modify-path
ENV PATH=$PATH:/etc/cargo/bin

RUN apt clean -y

ENV LLVM_CONFIG=llvm-config-${LLVM_VERSION}
ENV AFL_SKIP_CPUFREQ=1
ENV AFL_TRY_AFFINITY=1
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1

# Install AFL++
RUN git clone --depth=1 https://github.com/vanhauser-thc/afl-cov /home/maze/tools/afl-cov
RUN wget https://github.com/AFLplusplus/AFLplusplus/archive/refs/tags/v4.10c.tar.gz && \
    tar zxf v4.10c.tar.gz && rm v4.10c.tar.gz && \
    mv AFLplusplus-4.10c /home/maze/tools/AFLplusplus
WORKDIR /home/maze/tools/afl-cov
RUN make install
WORKDIR /home/maze/tools/AFLplusplus

# TODO: patch AFL++
RUN make clean && \
    make distrib && make install

USER maze

# Add scripts
ADD visualize_maze_cov.py /home/maze/tools/visualize_maze_cov.py
ADD get_coverage.sh /home/maze/tools/get_coverage.sh
ADD get_tcs.py /home/maze/tools/get_tcs.py
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py
ADD run_afl++.sh /home/maze/tools/run_afl++.sh
WORKDIR /home/maze/workspace
