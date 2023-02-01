class OptParser:
    def __init__(self) -> None:
        self.member = 1

    def parse(self, error=False):
        print("parse")
        if error:
            raise RuntimeError("parsing error")
        int("xxx")

class Profiler:
    def __init__(self) -> None:
        self.member = 2
        self.event_group = EventGroup()

    def profile(self, error=False):
        print("profile")
        self.event_group.get(error=True)

class Analyzer:
    def __init__(self) -> None:
        self.member = 3

    def analyze(self, error=False):
        print("analyze")
        if error:
            raise IOError("analyzing error")

class EventGroup:
    def __init__(self) -> None:
        self.member = 10

    def get(self, error=False):
        print("get event groups")
        if error:
            raise RuntimeError("fail to get event groups")

class Controller:
    def __init__(self) -> None:
        self.parser = OptParser()
        self.profiler = Profiler()
        self.analyzer = Analyzer()

    def hperf(self):
        try:
            self.parser.parse()
            self.profiler.profile()
            self.analyzer.analyze()
        except RuntimeError as e:
            print(e.args[0])
            exit(-1)
        except ValueError as e:
            print(e.args[0])
            exit(-1)
        finally:
            print("save log files")

# 主函数，调用Controller，Controller内部拥有（has）Parser，Profiler，Analyzer，而Profiler内部拥有EventGroup
# 在这样的情况下，测试如何在Controller内部实现统一的异常处理，即Parser，Profiler，Analyzer，EventGroup只负责抛出（raise）异常，Controller确定异常
if __name__ == "__main__":
    controller = Controller()
    controller.hperf()
