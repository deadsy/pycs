TOP = ../../..

SVD = STM32F401xE \
      STM32F401x \
      STM32F40x \

SVD_FILES = $(addsuffix .svd.gz,$(SVD)) 
PY_FILES = $(addsuffix .py,$(SVD)) 
PATCH_FILES = $(addsuffix .patch,$(SVD)) 

SVD2PY = $(TOP)/svd2py

%.py: %.svd.gz
	$(SVD2PY) $<

all:
	echo $(PY_FILES)
	echo $(PATCH_FILES)

