#!/bin/bash

cd $(dirname "$0")

# Set up simfactory2 (use defaults)
./Cactus/simfactory/bin/sim setup-silent

# Copy cosma8 config files to simfactory2 machine database
cp config/cosma8.ini Cactus/simfactory/mdb/machines/
cp config/cosma8.cfg Cactus/simfactory/mdb/optionlists/
cp config/cosma8.run Cactus/simfactory/mdb/runscripts/
cp config/cosma8.sub Cactus/simfactory/mdb/submitscripts/

# Build the code
cd Cactus
./simfactory/bin/sim build --thornlist=thornlists/ET_2025_05_reduced.th --machine=cosma8

