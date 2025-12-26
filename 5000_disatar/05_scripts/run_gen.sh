#!/bin/bash
echo "Starting population generation..." > /Users/ro9air/matsim-example-project/5000_disatar/05_scripts/gen.log
python3 /Users/ro9air/matsim-example-project/5000_disatar/05_scripts/generate_augmented_pop_280k.py >> /Users/ro9air/matsim-example-project/5000_disatar/05_scripts/gen.log 2>&1
echo "Finished population generation." >> /Users/ro9air/matsim-example-project/5000_disatar/05_scripts/gen.log
