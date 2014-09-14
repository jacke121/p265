import threading

class Consumer(threading.Thread):
    def __init__(self, q):
        super(Consumer, self).__init__()
        self.fifo = q

