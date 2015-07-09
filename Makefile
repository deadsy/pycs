all:
	make -C darm

clean:
	-rm *.pyc
	make -C darm clean
