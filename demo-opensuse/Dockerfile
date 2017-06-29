FROM opensuse:42.1
LABEL maintainer "root@shikherverma.com"

RUN zypper --non-interactive install git python-pip gcc python-devel libffi-devel libopenssl-devel vim build sudo osc wget tree rpm-build
RUN zypper --non-interactive install -t pattern devel_C_C++
RUN (cd home/ && git clone https://github.com/in-toto/in-toto.git)
RUN (cd home/ && git clone https://github.com/shikherverma/connman.git)
RUN (cd home/in-toto/ && pip install --upgrade pip setuptools && pip install -r requirements.txt && pip install -e .)
RUN echo "cd home/in-toto/" >> /etc/bash.bashrc

CMD ["/bin/bash"] 
