#!/bin/bash

cd $(dirname "$0")

# Download GetComponents script
curl -LO https://raw.githubusercontent.com/gridaphobe/CRL/refs/heads/master/GetComponents
chmod +x GetComponents

# Call GetComponents to download the necessary thorns
./GetComponents --root ./Cactus --noshallow ET_2025_05_reduced.th
