#!/usr/bin/env bash

venv="venv"
requirements="requirements.txt"
backend_entry_dir="./backend/"
backend_entry="main.py"

# Check dependencies

echo -n "Checking dependencies... "
for name in python pip virtualenv
do
  [[ $(which $name 2>/dev/null) ]] || { echo -en "\n$name needs to be installed.";deps=1; }
done
[[ $deps -ne 1 ]] && echo "OK" || { echo -en "\nInstall the above and rerun this script\n";exit 1; }

if [ -d "$venv" ]; then
  echo "virtualenv $venv found. Proceeding..."
else
  echo "virtualenv not found"
  echo "Creating $venv"
  virtualenv "$venv"
fi

echo "Activating virtualenv"
source "$venv/bin/activate"
echo "Installing packages"
pip install -r "$requirements"

echo "Running backend"
cd "$backend_entry_dir"
fastapi dev "$backend_entry"

