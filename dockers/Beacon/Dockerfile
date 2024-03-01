FROM maze-base

# Install dependencies
RUN apt update && apt -y upgrade && apt -y install make build-essential file

# Install Beacon
RUN git clone https://github.com/5hadowblad3/Beacon_artifact.git /home/maze/tools/beacon
WORKDIR /home/maze/tools/beacon
ENV BEACON=/home/maze/tools/beacon
RUN $BEACON/scripts/preinstall.sh

# 2.2.1 Build SVF
WORKDIR $BEACON
RUN git clone https://github.com/SVF-tools/SVF.git
WORKDIR ${BEACON}/SVF
RUN git reset --hard 3170e83b03eefc15e5a3707e5c52dc726ffcd60a && \
sed -i 's/LLVMRELEASE=\/home\/maze\/llvm-4.0.0\/llvm-4.0.0.obj/LLVMRELEASE=\/usr\/llvm/' build.sh && \
./build.sh

# 2.2.2 Build Precondition Inference Engine (precondInfer)
WORKDIR ${BEACON}/precondInfer
RUN rm -r build; mkdir build
WORKDIR ${BEACON}/precondInfer/build
RUN cmake \
	-DENABLE_KLEE_ASSERTS=ON \
	-DCMAKE_BUILD_TYPE=Release \
	-DLLVM_CONFIG_BINARY=/usr/bin/llvm-config \
	-DSVF_ROOT_DIR=${BEACON}/SVF \
	-DSVF_LIB_DIR=${BEACON}/SVF/Release-build/lib \
	.. && \
make -j$(nproc)
# 2.2.3 Build Instrumentation Engine (Ins)
WORKDIR ${BEACON}/Ins
RUN rm -r build; mkdir build
WORKDIR ${BEACON}/Ins/build
RUN CXXFLAGS="-fno-rtti" cmake \
	-DLLVM_DIR=/usr/lib/cmake/llvm/ \
	-DCMAKE_BUILD_TYPE=Release \
	.. && \
make -j$(nproc)

USER maze

ENV AFL_SKIP_CPUFREQ=1
ENV AFL_NO_AFFINITY=1
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1

# Add scripts
RUN pip3 install matplotlib
ADD get_coverage.sh /home/maze/tools/get_coverage.sh
ADD run_beacon.sh /home/maze/tools/run_beacon.sh
ADD get_tcs.py /home/maze/tools/get_tcs.py
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py
RUN wget -P /home/maze/tools/ https://raw.githubusercontent.com/sgzeng/Fuzzle/main/scripts/visualize_maze_cov.py

WORKDIR /home/maze/workspace
