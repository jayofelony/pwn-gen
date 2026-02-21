#!/bin/bash -e

echo -e "\e[32m### Installing PwnStore CLI ###\e[0m"
wget -q "https://raw.githubusercontent.com/wpa-2/pwnagotchi-store/main/pwnstore.py" \
    -O "${ROOTFS_DIR}/usr/bin/pwnstore"
chmod 755 "${ROOTFS_DIR}/usr/bin/pwnstore"
echo -e "\e[32m### PwnStore CLI installed ###\e[0m"
