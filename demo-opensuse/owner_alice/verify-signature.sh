#!/bin/bash
gunzip connman-1.30.tar.gz
gpg --import connman.keyring
gpg --verify connman-1.30.tar.sign connman-1.30.tar
