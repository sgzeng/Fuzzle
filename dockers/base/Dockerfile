FROM ubuntu:22.04

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
RUN chown -R maze:maze /home/maze
### Install common packages
RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install -y python3 python3-pip vim git wget sudo tree
RUN pip3 install pillow matplotlib
RUN echo 'maze  ALL=(root) NOPASSWD: ALL' >> /etc/sudoers
