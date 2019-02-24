PKG = darm-master

PATCHFILES = $(sort $(wildcard *.patch ))

PATCH_CMD = \
	for f in $(PATCHFILES); do\
	    echo $$f ":"; \
	    patch -d $(PKG) -p0 -b -z .original < $$f; \
	done

all:
	unzip -q $(PKG).zip
	$(PATCH_CMD)
	make -C $(PKG)

clean:
	-rm -rf $(PKG)
