import requests
import time
import sys
import os
import logging

from prometheus_client import Gauge, start_http_server

from info_config import prometheus_target_url
from info_config import job_filter

basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, basedir)

log_name = "{basedir}/exporter_status.log".format(basedir=basedir)
log = logging.getLogger(__name__)

formatter = logging.basicConfig(
    filename=log_name,
    level=logging.INFO,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S')


def prometheus_info_get(url):
    return_info = requests.get(url).content
    exporter_info = eval(return_info.decode('utf-8'))
    return exporter_info


def judge_type(job):
    for job_type in job_filter:
        if job == job_type:
            return 1
    return 0


def exporter_status_get(exporter_node_monitor):
    exporter_node_monitor._metrics.clear()
    exporters_info = prometheus_info_get(prometheus_target_url)
    active_targets = exporters_info.get('data').get('activeTargets')
    for exporter_info in active_targets:
        # print(exporter_info)
        health = exporter_info.get('health')
        target = exporter_info.get("discoveredLabels").get("__address__")
        job = exporter_info.get('discoveredLabels').get('job')
        if health == "down":
            exporter_status = 0
            if judge_type(job) == 1:
                continue
            log.info("{job} exporter instance down:{target}".format(job=job, target=target))
        elif health == "up":
            exporter_status = 1
        else:
            exporter_status = -1
        exporter_node_monitor.labels(target_exporter=target).set(exporter_status)


def main():
    exporter_node_monitor = Gauge('exporter_node', 'node available(1-up, 0-down)', ['target_exporter'])
    # otter_manager_gauge = Gauge('prometheus_target', 'node available(1-正常, 0-不正常)',
    #                             ['otter_manager_host', 'otter_manager_port'])
    start_http_server(10001)
    while True:
        exporter_status_get(exporter_node_monitor)
        # otter_manager_monitor(otter_manager_gauge, host=otter_manager_host, port=otter_manager_port)
        # otter_node_monitor(otter_node_gauge, node_info)
        time.sleep(5)


if __name__ == "__main__":
    main()
