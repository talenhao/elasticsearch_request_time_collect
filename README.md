# elasticsearch_request_time_collect
*收集es中指定索引中的所有request_time及request字段,并处理成报表.*

 ### elasticsearch_request_time_collect脚本使用说明

#### 激活python环境
source /virtual_python3.6.1/bin/activate

#### 用法：
```
/elasticsearch_request_time_collect.py [--命令选项] [参数]

命令选项：
    --help, -H                      帮助
    --version, -V                   输出版本号
    --index-regex -i                索引,支持正则 eg:in.access.log
    --date, -d                      收集的日期   eg:2017.08.16
    --es-ip -h                      Elasticsearch IP地址
    --es-port -p                    Elasticsearch 端口
```

#### 默认参数为:
```
    # default args
    es_host = "192.168.1.1"
    es_port = '9200'
    search_date = today
    index_regex = "*access.log"
```

#### eg:
```
time python elasticsearch_request_time_collect.py -i *access.log -d 2017.08.16 -h 192.168.1.1

...
api: '/adfafaf/sfdaf'
api: '/client/timeline/hadfasfafafasf'
api: '/client/adfasfsafasfasfasfaf'

real    0m32.262s
user    0m25.998s
sys     0m1.919s
```
