# -*-coding:utf-8-*-
# @Time:   2021/1/29 18:08
# @Author: FC
# @Email:  18817289038@163.com

import os
import inspect
import importlib


class LoadStrategy(object):

    filePath = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        self.classes = self.load_strategy_class_from_folder()

    def load_strategy_class_from_folder(self):

        strategyClass = {}
        for dirPath, dirNames, fileNames in os.walk(self.filePath):
            for fileName in fileNames:
                if fileName.startswith('__') or fileName[-3:] != '.py':
                    continue
                strategy_file_name = fileName[:-3]
                module = importlib.import_module('Strategy.Strategys.' + strategy_file_name)
                for class_name in dir(module):
                    if class_name.endswith('Strategy'):
                        value = getattr(module, class_name)
                        strategyClass[value.__name__] = value

        return strategyClass


if __name__ == '__main__':
    S = LoadStrategy()
    S.load_strategy_class_from_folder()
