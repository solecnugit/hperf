import logging

# 获得Logger对象
# 系统中Logger对象，不能被直接实例化，获取Logger对象的方法为 getLogger()，并且这里运用了单例模式。
# 这样的好处在于，对于程序中不同的类需要使用logging，不需要通过构造函数传入logger实例的引用，
# 直接通过logging模块提供的getLogger()方法来获得Logger对象即可
logger_a = logging.getLogger("a")
logger_b = logging.getLogger("b")

# 默认的Logger对象，只会记录30以上的记录，需要独立设置
# DEBUG=10 < INFO=20 < WARNING=30 < ERROR=40 < CRITICAL=50
logger_a.setLevel(logging.DEBUG)
logger_b.setLevel(logging.DEBUG)

# Logger对象负责收集记录信息，而Handler对象负责格式化输出记录信息
handler_stream = logging.StreamHandler()    # 控制台
handler_file = logging.FileHandler("./test.log")    # 文本文件

# 设置Formatter绑定到Handler，以设置输出记录的格式
formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")
handler_stream.setFormatter(formatter)
handler_file.setFormatter(formatter)

# 将Handler绑定到Logger，使之生效
logger_a.addHandler(handler_stream)
logger_a.addHandler(handler_file)
logger_b.addHandler(handler_stream)
logger_b.addHandler(handler_file)

logger_a.debug("1")
logger_a.info("2")
logger_a.warning("3")
logger_a.error("4")

logger_b.debug("5")
logger_b.info("6")
logger_b.warning("7")
logger_b.error("8")

