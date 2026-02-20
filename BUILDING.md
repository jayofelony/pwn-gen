# Building Pwnagotchi Images

This guide covers everything you need to build a Pwnagotchi image from scratch using pwn-gen.

## Requirements

- Ubuntu 22.04 or later (native build) **or** any Linux system with Docker installed
- ~20GB free disk space
- Internet connection (the build downloads packages)

---

## Option 1: Native Build

### Install Prerequisites

```bash
sudo apt-get install -y \
  git quilt qemu-user-static debootstrap zerofree \
  libarchive-tools curl pigz arch-test qemu-utils \
  qemu-system-arm qemu-user \
  gcc-aarch64-linux-gnu gcc-arm-linux-gnueabihf
```

### Build

```bash
# Clone the repo
git clone https://github.com/jayofelony/pwn-gen
cd pwn-gen

# 64-bit image (Pi Zero 2W, Pi 3, Pi 4)
make 64bit

# 32-bit image (original Pi Zero W)
make 32bit
```

The finished image will be in `~/images/` when the build completes (expect 1-2 hours).

---

## Option 2: Docker Build

Docker gives you a clean, isolated build environment without installing anything on your host machine beyond Docker itself.

### Install Docker

```bash
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER
# Log out and back in for the group change to take effect
```

### Build

```bash
# Clone the repo
git clone https://github.com/jayofelony/pwn-gen
cd pwn-gen

# 64-bit image (Pi Zero 2W, Pi 3, Pi 4)
./pi-gen-64bit/build-docker.sh -c config-64bit

# 32-bit image (original Pi Zero W)
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

---

## Overriding Build Paths

By default the build uses your current user and home directory. If you need to
override these (e.g. building as a different user or to a custom location):

```bash
make 64bit BUILD_USER=myuser
make 64bit BUILD_USER=myuser BUILD_HOME=/custom/home
make 64bit IMAGE_DIR=/mnt/storage/images
```

---

## Flashing the Image

Once the build completes, flash the `.img.xz` file from `~/images/` using
[Raspberry Pi Imager](https://www.raspberrypi.com/software/) or `dd`:

```bash
# Find your SD card device first - be careful to get the right one!
lsblk

# Flash with dd (replace sdX with your actual device)
xzcat ~/images/your-image.img.xz | sudo dd of=/dev/sdX bs=4M status=progress
sync
```

---

## After Flashing

Copy your `config.toml` to `/etc/pwnagotchi/config.toml` on the boot partition,
then insert the card and power on. On first boot the device will take a few
minutes to initialise.

If you don't have a config yet, the device will boot with defaults and you can
configure it via the web UI or SSH.
