
SVD2PY = $(TOP)/svd2py

PY_FILES = $(patsubst %, %.py, $(FILES)) 

%.py: ./svd/%.svd.gz
	@echo "[svd2py]" $*
	@$(SVD2PY) $< $@

svdtest: $(PY_FILES)

clean:
	-rm *.pyc
	-rm *.py.original
	-rm $(PY_FILES)
