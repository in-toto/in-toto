#!/bin/bash

for i in archiso debian django gcc tails simple_layout
do
    python ${i}.py > $i.layout
done

a2ps -R -f 6 *.layout -o layouts.ps
ps2pdf layouts.ps metadata_sketches.pdf
