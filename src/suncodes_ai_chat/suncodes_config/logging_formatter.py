import json
import logging
from datetime import datetime

from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        levelname_color = {
            "DEBUG": Fore.BLUE,
            "INFO": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "CRITICAL": Style.BRIGHT + Fore.RED,
        }
        reset = Style.RESET_ALL
        record.levelname = f"{levelname_color.get(record.levelname, '')}{record.levelname}{reset}"
        record.module = f"{Fore.GREEN}{record.module}{reset}"
        record.name = f"{Fore.GREEN}{record.name}{reset}"
        record.funcName = f"{Fore.GREEN}{record.funcName}{reset}"
        # 确保原日志内容的换行符不会丢失
        formatted_message = super().format(record)
        return formatted_message


class PackageFilter(logging.Filter):
    def filter(self, record):
        # 为日志记录添加自定义属性
        if record.pathname:
            record.packagename = record.pathname.replace("/", ".").replace("\\", ".").removesuffix(".py")
        else:
            record.packagename = "unknown"
        return True


REMOVE_ATTR = ["filename", "module", "exc_text", "stack_info", "created", "msecs", "relativeCreated", "exc_info",
               "msg", "args"]


class JSONLoggingFormatter(logging.Formatter):
    """JSON 格式日志输出"""

    # host_name, host_ip = HostIp.get_host_ip()

    def format(self, record):
        extra = self.build_record(record)
        self.set_format_time(extra)  # set time
        # self.set_host_ip(extra)  # set host name and host ip
        if isinstance(record.msg, dict):
            # 如果是字典，直接输出
            extra['msg'] = record.msg
        else:
            if record.args:
                # 字符串模板，格式化 print("I'm %s. I'm %d year old" % ('Vamei', 99))
                extra['msg'] = record.msg % record.args
            else:
                extra['msg'] = record.msg
        if record.exc_info:
            extra['exc_info'] = self.formatException(record.exc_info)

        suncodes_log = {
            '@timestamp': extra.get('@timestamp'),
            '@version': 1,
            'message': '{} {}'.format(extra.get('msg', ''), extra.get('exc_info', '')),
            'logger_name': f"{extra.get('name')}.{extra.get('funcName')}",
            'level': extra.get('levelname'),
            'level_value': extra.get('levelno') * 1000,
            'thread_name': extra.get('threadName'),
        }

        if self._fmt == 'pretty':
            return json.dumps(suncodes_log, indent=1, ensure_ascii=False)
        else:
            return json.dumps(suncodes_log, ensure_ascii=False)

    def formatStack(self, stack_info):
        return stack_info

    @classmethod
    def build_record(cls, record):
        return {
            attr_name: record.__dict__[attr_name]
            for attr_name in record.__dict__
            if attr_name not in REMOVE_ATTR
        }

    @classmethod
    def set_format_time(cls, extra):
        now = datetime.utcnow()
        format_time = now.strftime("%Y-%m-%dT%H:%M:%S" + ".%03d" % (now.microsecond / 1000) + "Z")
        extra['@timestamp'] = format_time
        return format_time
