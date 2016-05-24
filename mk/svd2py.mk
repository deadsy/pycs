
SVD2PY = $(TOP)/tools/svd2py
PATCH = patch

PY_FILES = $(patsubst %, %.py, $(FILES)) 

%.py: ./svd/%.svd.gz
	$(SVD2PY) $< $@
	if [ -e $*.patch ]; then $(PATCH) -i $*.patch -b --suffix .original; fi;

all: $(PY_FILES)

clean:
	-rm *.pyc
	-rm *.py.original
	-rm $(PY_FILES)
