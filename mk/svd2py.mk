
SVD2PY = $(TOP)/svd2py

SVD_FILES = $(wildcard ./svd/*.svd.gz)
PY_FILES = $(patsubst ./svd/%.svd.gz, %.py, $(SVD_FILES)) 

%.py: ./svd/%.svd.gz
	@echo "[svd2py]" $*
	@$(SVD2PY) $< $@

svdtest: $(PY_FILES)

clean:
	-rm *.pyc
	-rm $(PY_FILES)
