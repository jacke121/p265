import threading

class Producer(threading.Thread):
    def __init__(self, q):
        super(Producer, self).__init__()
        self.fifo =  q
