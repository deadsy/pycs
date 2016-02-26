
OUT = jlink_test

SRC = main.c \

OBJ = $(patsubst %.c, %.o, $(wildcard *.c))

CFLAGS = -Wall -Wextra -Wstrict-prototypes
CFLAGS += -Werror

LDFLAGS = -L /home/jasonh/tmp/JLink_Linux_V510o_x86_64
LIBS = -ljlinkarm

.c.o:
	$(CC) $(CFLAGS) -c $< -o $@

all: $(OUT)

$(OUT): $(OBJ)
	$(CC) $(LDFLAGS) $(OBJ) $(LIBS) -o $@

clean:
	-rm $(OBJ)
	-rm $(OUT)
