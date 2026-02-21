#!/bin/bash -e

PWNSTORE_RAW="https://raw.githubusercontent.com/wpa-2/pwnagotchi-store/main"

echo -e "\e[32m### Installing PwnStore CLI ###\e[0m"
wget -q "${PWNSTORE_RAW}/pwnstore.py" -O "${ROOTFS_DIR}/usr/bin/pwnstore"
chmod 755 "${ROOTFS_DIR}/usr/bin/pwnstore"

echo -e "\e[32m### Installing PwnStore UI plugin ###\e[0m"
wget -q "${PWNSTORE_RAW}/pwnstore_ui.py" \
    -O "${ROOTFS_DIR}/usr/local/share/pwnagotchi/custom-plugins/pwnstore_ui.py"

echo -e "\e[32m### PwnStore installed ###\e[0m"
