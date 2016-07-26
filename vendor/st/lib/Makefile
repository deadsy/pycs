
# cross compilation tools
XTOOLS_DIR = /opt/gcc-arm-none-eabi-5_4-2016q2
X_CC = $(XTOOLS_DIR)/bin/arm-none-eabi-gcc
X_OBJDUMP = $(XTOOLS_DIR)/bin/arm-none-eabi-objdump

SRC = stm32f4_flash.S \

OBJ = $(SRC:.S=.o)

.S.o: 
	$(X_CC) -c $<
	$(X_OBJDUMP) -S $@

all: $(OBJ)

clean:
	-rm $(OBJ)
