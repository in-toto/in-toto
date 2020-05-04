# Choose a base image with a larges number of packages out of the box, so that
# in-toto inspections containing arbitrary commands are likely to succeed.
FROM ubuntu:latest

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y python3-pip \
    && apt-get autoremove \
    && apt-get autoclean \
    && pip3 --no-cache install in-toto