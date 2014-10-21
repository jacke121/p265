go:
	./p265 -b sanity.bin

log: logs/p265.log
	cd logs && python ../tools/gen_logs.py

clean:
	rm logs/*.log

diff:
	diff logs/frame0_ctu0.log test/golden/frame0_ctu0.log

check: log
	diff logs/frame0_ctu0.log test/golden/frame0_ctu0.log
	diff logs/frame0_ctu29.log test/golden/frame0_ctu29.log
	diff logs/frame1_ctu0.log test/golden/frame1_ctu0.log
	diff logs/frame1_ctu29.log test/golden/frame1_ctu29.log
	diff logs/frame2_ctu0.log test/golden/frame2_ctu0.log
	diff logs/frame2_ctu29.log test/golden/frame2_ctu29.log
