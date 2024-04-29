FROM maze-beacon-prebuilt

# Add scripts
ADD get_coverage.sh /home/maze/tools/get_coverage.sh
ADD monitor.py /home/maze/tools/visualize_maze_cov.py
ADD run_beacon.sh /home/maze/tools/run_beacon-prebuilt.sh
ADD get_tcs.py /home/maze/tools/get_tcs.py
ADD convert_to_cov_code.py /home/maze/tools/convert_to_cov_code.py

WORKDIR /home/maze/workspace
