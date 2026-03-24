#!/bin/bash

cd $(dirname "$0")

# Set up simfactory2 (use defaults)
./Cactus/simfactory/bin/sim setup-silent

# Copy Tursa config files to simfactory2 machine database
cp config/tursa.ini Cactus/simfactory/mdb/machines/
cp config/tursa.cfg Cactus/simfactory/mdb/optionlists/
cp config/tursa.run Cactus/simfactory/mdb/runscripts/
cp config/tursa.sub Cactus/simfactory/mdb/submitscripts/

# Build the code
cd Cactus
./simfactory/bin/sim build --thornlist=thornlists/ETK-CarpetX-subcycling.th --machine=tursa
