all:
	make -C darm

svdtest:
	make -C vendor $@

clean:
	-rm *.pyc
	-rm target/*.pyc
	make -C darm $@
	make -C vendor $@
