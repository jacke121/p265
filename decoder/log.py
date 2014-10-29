import sys
import logging

class MainFormatter(logging.Formatter):
    def format(self, record):
        if record.name == "p265":
            return "%s" % record.getMessage()
        elif record.name == "p265.location":
            return "[location] %s" % record.getMessage()
        elif record.name == "p265.syntax_element":
            return "[syntax_element] %s" % record.getMessage()
        elif record.name == "p265.cabac":
            return "[cabac] %s" % record.getMessage()

class MainStreamFilter(logging.Filter):
    def filter(self, record):
        if record.name == "p265":
            return 1
        elif record.name == "p265.location":
            return 1
        elif record.name == "p265.syntax_element":
            return 0
        elif record.name == "p265.cabac":
            return 0

def create_main_logger():
    main = logging.getLogger("p265")
    main.setLevel(logging.DEBUG)

    f_handler = logging.FileHandler(filename="logs/p265.log", mode='w')
    f_handler.setLevel(logging.DEBUG)
    s_handler = logging.StreamHandler(stream = sys.stdout)
    s_handler.setLevel(logging.INFO)

    formatter = MainFormatter()
    f_handler.setFormatter(formatter)
    s_handler.setFormatter(formatter)
    
    s_filter = MainStreamFilter()
    s_handler.addFilter(s_filter) # Only location information will be output to sys.stdout

    main.addHandler(f_handler)
    main.addHandler(s_handler)
    return main

def create_location_logger():
    location = logging.getLogger("p265.location")
    handler = logging.FileHandler(filename="logs/location.log", mode='w')
    handler.setFormatter(logging.Formatter(fmt="%(message)s"))
    location.addHandler(handler)
    return location

def create_syntax_logger():
    syntax = logging.getLogger("p265.syntax_element")
    handler = logging.FileHandler(filename="logs/syntax_element.log", mode='w')
    handler.setFormatter(logging.Formatter(fmt="%(message)s"))
    syntax.addHandler(handler)
    return syntax

def create_cabac_logger():
    cabac = logging.getLogger("p265.cabac")
    handler = logging.FileHandler(filename="logs/cabac.log", mode='w')
    handler.setFormatter(logging.Formatter(fmt="%(message)s"))
    cabac.addHandler(handler)
    return cabac

def create_qp_logger():
    qp = logging.getLogger("p265.qp")
    handler = logging.FileHandler(filename="logs/qp.log", mode='w')
    handler.setFormatter(logging.Formatter(fmt="%(message)s"))
    qp.addHandler(handler)
    return qp

main = create_main_logger()
location = create_location_logger()
syntax = create_syntax_logger()
cabac = create_cabac_logger()
qp = create_qp_logger()

if __name__ == "__main__":
    import os
    if not os.path.exists("./logs"):
        os.mkdir("./logs")
    print main.handlers
    print syntax.handlers
    print location.handlers
    print cabac.handlers
    print main.level
    main.info("Hello main")
    main.error("Hello main error")
    syntax.info("pps_id = %d" % 1)
    location.info("hello location")
