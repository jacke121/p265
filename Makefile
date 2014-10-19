go:
	./p265 -b sanity.bin

log:
	cd logs && python ../tools/gen_logs.py
