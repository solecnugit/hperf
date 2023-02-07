import logging

# 获得Logger对象
# 系统中Logger对象，不能被直接实例化，获取Logger对象的方法为 getLogger()，并且这里运用了单例模式。
# 这样的好处在于，对于程序中不同的类需要使用logging，不需要通过构造函数传入logger实例的引用，
# 直接通过logging模块提供的getLogger()方法来获得Logger对象即可
logger = logging.getLogger("hperf")
# logger_a = logging.getLogger("a")
# logger_b = logging.getLogger("b")

# 默认的Logger对象，只会记录30以上的记录，需要独立设置
# DEBUG=10 < INFO=20 < WARNING=30 < ERROR=40 < CRITICAL=50
logger.setLevel(logging.DEBUG)

# Logger对象负责收集记录信息，而Handler对象负责格式化输出记录信息
handler_stream = logging.StreamHandler()    # 控制台
handler_stream.setLevel(logging.DEBUG)    # 控制台输出级别为warning以上
handler_file = logging.FileHandler("./test.log", "w")    # 文本文件
handler_file.setLevel(logging.DEBUG)    # 文本文件输出级别为debug以上

# 设置Formatter绑定到Handler，以设置输出记录的格式
formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")
handler_stream.setFormatter(formatter)
handler_file.setFormatter(formatter)

# 将Handler绑定到Logger，使之生效
logger.addHandler(handler_stream)

logger_a = logging.getLogger("hperf.a")

logger_a.debug("1")
logger_a.info("2")
logger_a.warning("3")
logger_a.error("4")

logger.addHandler(handler_file)

logger_a.debug("5")
logger_a.info("6")
logger_a.warning("7")
logger_a.error("8")

handler_stream.setLevel(logging.WARNING)

logger_a.debug("9")
logger_a.info("10")
logger_a.warning("11")
logger_a.error("12")