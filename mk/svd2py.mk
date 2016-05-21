
SVD2PY = $(TOP)/tools/svd2py

PY_FILES = $(patsubst %, %.py, $(FILES)) 

%.py: ./svd/%.svd.gz
	$(SVD2PY) $< $@

all: $(PY_FILES)

clean:
	-rm $(PY_FILES)
