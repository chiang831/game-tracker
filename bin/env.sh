#!/bin/bash

GITROOT=$(git rev-parse --show-toplevel)

export PATH=$GITROOT/bin:$PATH
export PYTHONPATH=$GITROOT:$PYTHONPATH
