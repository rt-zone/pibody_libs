# ARTIWARE

# Artisan's Firmware

This repository prerequisites micropython to be installed and set up. See section below on detailed instruction

This folder contains config files to make a firmware for:

- **PiBody**
- **ATLAS**
- **PiSP (Under construction)**

### How to use it?

* Install micropython alongisde this repository
  * By default, makefile sets micropython location in a same directory of this file, if you don't have micropython in neighboring directory, specify it in the makefile's `MP_PATH` variable
  * Don't forget to prepare micropython if you fresh cloned micropython

    * Checkout to the stable version

      ```
      git fetch --tags
      git tag # To view available versions
      git checkout v1.28.0 # Or any stable version of your choice
      git checkout -b pibody-v1.28.0 # Create branch to attach detached HEAD
      ```
    * Make mpy-cross. In micropython directory root:

      ```
      make -C mpy-cross 
      ```
    * Build submodules for **Pico W**

      ```
      cd ports/rp2
      make BOARD=RPI_PICO_W submodules
      ```
* Default target platform is **PiBody**, you need to specify board name (i.e. `BOARD=ATLAS`) to target other platforms for the following commands:
* Run `make` to build a firmware
* Firmware binary files are located at **build/_board name_/** folder
* Run `make deploy` to upload the firmware to the **Pico **(make sure that pico is in bootsel mode)
* Run `make clean` to delete build folder
```bash
# 1. Clone MicroPython
cd
git clone https://github.com/micropython/micropython.git
cd micropython

# 2. Build mpy-cross
make -C mpy-cross

# 3. Pulling submodules for rp2
cd ports/rp2
make submodules

cd ~/Artiware
# 4. Build firmware with castom board
make BOARD=PISP \
     BOARD_DIR=/path/to/boards/PiSP \
     USER_C_MODULES=/path/to/boards/PiSP/cmodules/micropython.cmake
```
```bash
# analog
cd ~/Artiware
make BOARD=PiSP clean
make BOARD=PiSP
make BOARD=PiSP
```