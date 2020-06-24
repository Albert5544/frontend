from abc import abstractmethod, ABCMeta


class language_interface(object):
    __metaclass__ = ABCMeta  # 指定这是一个抽象类

    @abstractmethod  # 抽象方法
    def build_docker_file(self, current_user_id, name, ):
        pass

    def Marlon(self):
        pass
