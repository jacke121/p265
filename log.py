import sys
import logging

logging.basicConfig(level=logging.DEBUG, format="%(message)s")
#logging.basicConfig(level=logging.DEBUG)

class P265Formatter(logging.Formatter):
    def format(self, record):
        if record.name == "p265":
            return "%s" % record.getMessage()
        elif record.name == "p265.syntax_element":
            return "[syntax_element] %s" % record.getMessage()
        elif record.name == "p265.location":
            return "[location] %s" % record.getMessage()
        elif record.name == "p265.cabac":
            return "[cabac] %s" % record.getMessage()

formatter = P265Formatter()

def create_main_logger():
    main = logging.getLogger("p265")
    f_handler = logging.FileHandler(filename="logs/p265.log", mode='w')
    #s_handler = logging.StreamHandler(stream = sys.stdout)
    f_handler.setFormatter(formatter)
    #s_handler.setFormatter(formatter)
    main.addHandler(f_handler)
    #main.addHandler(s_handler)
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

main = create_main_logger()
location = create_location_logger()
syntax = create_syntax_logger()
cabac = create_cabac_logger()

if __name__ == "__main__":
    main.info("Hello main")
    syntax.info("pps_id = %d" % 1)
    location.info("hello location")
