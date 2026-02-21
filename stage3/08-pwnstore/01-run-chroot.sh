#!/bin/bash -e

echo -e "\e[32m### Verifying PwnStore ###\e[0m"
source /home/pi/.pwn/bin/activate
python3 -c "import requests; print('[+] requests', requests.__version__)" \
    || { echo -e "\e[31m[!] requests missing from venv\e[0m"; exit 1; }
deactivate
echo -e "\e[32m### PwnStore OK ###\e[0m"
