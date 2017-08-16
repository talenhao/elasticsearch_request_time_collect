#!/usr/bin/env python3.6
# -*- coding:UTF-8 -*-

"""

"""

import elasticsearch
from elasticsearch import helpers
# for log
import logging
import datetime
import time
import os
import sys
import urllib3
import socket
import prettytable
import getopt

# user args
__author__ = "Tianfei Hao(天飞)<talenhao@gmail.com>"
__status__ = "product"
__version__ = "2017.08.16"
__create_date__ = "2017.08.15"
__last_date__ = __version__


# log args
class GetLogger:
    def __init__(self, log_path, logger_name, logging_level):
        self.log_path = log_path
        self.logger_name = logger_name
        self.logging_level = logging_level
        self.agent_logger = logging.getLogger(self.logger_name)
        self.agent_logger.setLevel(self.logging_level)

        # agent_logger.error('Failed to open file', exc_info=True)
    def get_l(self):
        # logging.config.fileConfig('logging.conf')

        # create root logger
        # logging.basicConfig(level=logging.NOTSET)

        # 创建file handler,写入日志文件
        logfile_handler = logging.FileHandler(self.log_path)
        # logfile_handler = RotatingFileHandler(self.log_path, backupCount=5)
        logfile_handler.setLevel(logging.DEBUG)
        # 创建console handler 同时输出到stdout
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建formatter
        logfile_fmt_str = '%(asctime)-15s %(levelname)-5s ScriptFile: %(filename)s Funcation: %(funcName)s ' \
                          'line:+%(lineno)d [%(threadName)s] %(name)s %(message)s'
        logfile_formatter = logging.Formatter(logfile_fmt_str)
        # console_fmt_str = "%(asctime)-15s %(levelname)-5s %(threadName)s %(message)s"
        console_fmt_str = "%(message)s"
        console_formatter = logging.Formatter(console_fmt_str)

        # handler set formatter
        logfile_handler.setFormatter(logfile_formatter)
        console_handler.setFormatter(console_formatter)

        # add handler and formatter to logger
        self.agent_logger.addHandler(logfile_handler)
        self.agent_logger.addHandler(console_handler)
        return self.agent_logger


LogPath = '/tmp/%s.log.%s' % (os.path.basename(__file__), datetime.datetime.now().strftime('%Y-%m-%d,%H.%M'))
c_logger = GetLogger(LogPath, __name__, logging.DEBUG).get_l()
today = datetime.date.fromtimestamp(time.time())
c_logger.debug("today is : %s", today)


all_args = sys.argv[1:]
usage = '''
用法：
%s [--命令选项] [参数]

命令选项：
    --help, -H                      帮助
    --version, -V                   输出版本号
    --index-regex -i                索引,支持正则 eg:in.itugo.com.access.log
    --date, -d                      收集的日期   eg:2017.08.16
    --es-ip -h                      Elasticsearch IP地址
    --es-port -p                    Elasticsearch 端口
''' % sys.argv[0]


def get_options():
    """
    处理命令行参数
    :return:
    """
    # default args
    es_host = "192.168.1.94"
    es_port = '9200'
    search_date = today
    index_regex = "in.itugo.com.access.log"
    if all_args:
        c_logger.debug("命令行参数是 %s", str(all_args))
    else:
        c_logger.error(usage)
        sys.exit()
    try:
        opts, args = getopt.getopt(all_args, "HVd:i:h:p:",
                                   ["help", "version", "date=", "index-regex=", "es-ip=", "es-port="])
    except getopt.GetoptError:
        c_logger.error(usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-H', "--help"):
            c_logger.info(usage)
            sys.exit()
        elif opt in ("-V", "--version"):
            print('Current version is %0.2f' % float(__version__))
            c_logger.debug('Version %s', __version__)
            sys.exit()
        elif opt in ("-i", "--index-regex"):
            index_regex = arg
        elif opt in ("-d", "--date"):
            c_logger.info("日期 %s", arg)
            search_date = arg
        elif opt in ("-h", "--ex-ip"):
            es_host = arg
        elif opt in ("-p", "--es-port"):
            es_port = arg
    return index_regex, search_date, es_host, es_port


# output table format
def create_pretty_table(title, table_content):
    """
    输出为表格
    :param title:
    :param table_content: {{"request": "name", "count": "count", "average": "average"},{}...}
    :return: table_content
    """
    pretty_table = prettytable.PrettyTable(["API", "count(>=1s)", "average(Statistics only > 1s)"])
    pretty_table.align = "l"  # Left align
    pretty_table.padding_width = 1  # One space between column edges and contents (default)
    pretty_table.header = True
    for name, item in table_content.items():
        c_logger.debug('%r,%r', name, item)
        if item:
            pretty_table.add_row([item['request'], item['count'], item['average']])
    # message = "%s" % (title + pretty_table.get_html_string(format=True))
    # 按数量倒排列
    message = "%s" % (title + '\n' + pretty_table.get_string(format=True, sortby='count(>=1s)', reversesort=True))
    c_logger.debug('message: %r', message)
    return message


def produce_table_content(apis, request_dict):
    table_content = {}
    for api in apis:
        api_sum = str(api) + '_sum'
        api_count = str(api) + '_count'
        c_logger.info("api: %r", api)
        count = request_dict[api_count]
        average = request_dict[api_sum]/request_dict[api_count]
        # 统一保留3位小数
        average = "%.3f" % average
        table_content[api] = {"request": api, "count": count, "average": average}
    return table_content


def main():
    index_regex, search_date, es_host, es_port = get_options()
    es_ip_port = es_host + ':' + es_port
    es_indices_range = index_regex + "-" + search_date
    es_client = elasticsearch.Elasticsearch(hosts=es_ip_port)
    # for es 5.x版本
    query = {
        "_source": {
            "includes": ["request_time", "request"]
        },
        "query": {
            "bool": {
                "must": {
                    "exists": {
                        "field": "request_time"
                    }
                },
                "must": {
                    "exists": {
                        "field": "request"
                    }
                },
                "filter": {
                    "range": {
                        "request_time": {
                            "gte": 1
                        }
                    }
                }
            }
        }
    }
    # for es 2.x版本 5.x版本不再支持field多字段
    # query = {
    #     "_source": {
    #         "includes": ["request_time", "request"]
    #     },
    #     "query": {
    #         "bool": {
    #             "must": {
    #                 "exists": {
    #                     "field": ["request_time", "request"]
    #                 }
    #             },
    #             "filter": {
    #                 "range": {
    #                     "request_time": {"gte": 1}
    #                 }
    #             }
    #         }
    #     }
    # }
    try:
        # results = es_client.search(index=es_indices_range, body=query)
        results = helpers.scan(client=es_client, index=es_indices_range, scroll=u'30m', query=query,
                               request_timeout=300)
    except socket.timeout:
        c_logger.error('scroll 时间太短.')
    except elasticsearch.exceptions.ConnectionTimeout:
        c_logger.error('超时')
    # c_logger.info(results)
    # for r in results:
    #     print(r)
    # create dict
    request_dict = {}
    # 取出每个hit
    # for hit in results['hits']['hits']:
    for hit in results:
        # 1.取出 api and request time
        hit_request = hit['_source']['request']
        hit_request_time = hit['_source']['request_time']
        c_logger.info("%r: %r", hit_request, hit_request_time)
        # 2.创建列表
        if 'i_l' not in vars():
            i_l = []
        else:
            if hit_request not in i_l:
                i_l.append(hit_request)
        # create dict key
        request_sum = str(hit_request) + '_sum'
        request_count = str(hit_request) + '_count'
        if request_sum not in request_dict and request_count not in request_dict:
            request_dict[request_sum] = hit_request_time
            request_dict[request_count] = 1
        else:
            request_dict[request_sum] += hit_request_time
            request_dict[request_count] += 1
    # c_logger.debug(request_dict)
    title = "%r 接口request_time统计" % search_date
    table_content = produce_table_content(i_l, request_dict)
    table = create_pretty_table(title=title, table_content=table_content)
    # c_logger.info("%r", table)
    filename = 'api_request_time_gte_1s-%s-%s.txt' % (index_regex, search_date)
    with open(filename, mode='w') as writefile:
        writefile.write(table)
        # print('\n' + table)


if __name__ == '__main__':
    main()
