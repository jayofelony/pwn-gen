# pwn-gen

Image builder for [Pwnagotchi](https://pwnagotchi.org/) based on [pi-gen](https://github.com/RPi-Distro/pi-gen).

Produces ready-to-flash `.img.xz` images for both 32-bit (Pi Zero W) and 64-bit (Pi Zero 2W, Pi 3, Pi 4, Pi 5) hardware.

---

## Prerequisites

~20GB free disk space and the following packages:

```bash
sudo apt-get install -y \
  git quilt qemu-user-static debootstrap zerofree \
  libarchive-tools curl pigz arch-test qemu-utils \
  qemu-system-arm qemu-user \
  gcc-aarch64-linux-gnu gcc-arm-linux-gnueabihf
```

---

## Building — Native

```bash
# Clone the repo
git clone https://github.com/jayofelony/pwn-gen
cd pwn-gen

# 64-bit (Pi Zero 2W, Pi 3, Pi 4, Pi 5)
make 64bit

# 32-bit (original Pi Zero W)
make 32bit
```

Finished images are placed in `~/images/`.

---

## Building — Docker

```bash
# Install Docker
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER
# Log out and back in after this

# 64-bit
./pi-gen-64bit/build-docker.sh -c config-64bit

# 32-bit
./pi-gen-32bit/build-docker.sh -c config-32bit
```

---

## Which image do I need?

| Device | Image |
|--------|-------|
| Pi Zero W (original) | 32-bit |
| Pi Zero 2W | 64-bit |
| Pi 3 | 64-bit |
| Pi 4 | 64-bit |
| Pi 5 | 64-bit |

---

## Configuration

Before building, check the config files:

- `config-64bit` — settings for the 64-bit build
- `config-32bit` — settings for the 32-bit build

The image name is automatically populated from the pwnagotchi version in `_version.py`.

You can override build paths at the command line if needed:

```bash
make 64bit BUILD_USER=myuser
make 64bit IMAGE_DIR=/mnt/storage/images
```

---

## Flashing

Flash the resulting `.img.xz` from `~/images/` using [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or `dd`:

```bash
# Find your SD card device first - be careful to get the right one!
lsblk

# Flash with dd (replace sdX with your actual device)
xzcat ~/images/your-image.img.xz | sudo dd of=/dev/sdX bs=4M status=progress
sync
```

After flashing, copy your `config.toml` to `/etc/pwnagotchi/` on the boot partition before first boot.

---

## Links

- [Pwnagotchi Project](https://pwnagotchi.org/)
- [Pwnagotchi GitHub](https://github.com/jayofelony/pwnagotchi)
- [PwnStore](https://pwnstore.org/)
- [Community Support](https://pwnstore.org/troubleshoot.html)
