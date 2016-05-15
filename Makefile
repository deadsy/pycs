all:
	make -C darm

clean:
	-rm *.pyc
	-rm target/*.pyc
	make -C darm clean
