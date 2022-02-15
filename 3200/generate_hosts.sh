#!/bin/bash
touch hostfile
rocks list host | grep compute | cut -d" " -f1 | sed 's/.$//' | shuf | head -n $1 > hostfile
