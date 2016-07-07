
SVD2PY = $(TOP)/svd2py
XSD =  $(TOP)/vendor/arm/CMSIS-SVD_Schema_1_1_draft.xsd

SVD_FILES = $(wildcard ./svd/*.svd.gz)
PY_FILES = $(patsubst ./svd/%.svd.gz, %.py, $(SVD_FILES)) 

%.py: ./svd/%.svd.gz
	@#echo "[xmllint]" $*
	@#xmllint --noout --schema $(XSD) $<
	@echo "[svd2py]" $*
	@$(SVD2PY) $< $@

svdtest: $(PY_FILES)

clean:
	-rm *.pyc
	-rm $(PY_FILES)
