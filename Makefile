all:
	make -C darm
	make -C soc

clean:
	-rm *.pyc
	-rm target/*.pyc
	make -C darm $@
	make -C soc $@
