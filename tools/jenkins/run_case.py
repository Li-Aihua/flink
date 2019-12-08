#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

# This file will be runned by jenkis to run the e2e perf test
# Params:
# am_seserver_dddress: master machines's ip  of standalone environment
# scenario_file: the file which contains test scenarios
# flink_home: the path of flink
# inter_nums：the num of every scenario's running, default value is 10
# wait_minute: interval time of two elections of qps,default value is 10s
#


import sys
import time
import re

if sys.version_info < (3, 5):
    print("Python versions prior to 3.5 are not supported.")
    sys.exit(-1)

from logger import logger
from utils import run_command
from restapi_common import get_avg_qps_by_restful_interface


def start_server(flink_home):
    cmd = "bash %s/bin/start-cluster.sh" % flink_home
    status, output = run_command(cmd)
    if status and output.find("Exception") < 0:
        return True
    else:
        return False


def end_server(flink_home):
    cmd = "bash %s/bin/stop_yarn.sh" % flink_home
    status, output = run_command(cmd)
    if status and output.find("Exception") < 0:
        return True
    else:
        return False


def get_scenarios(scenario_file_name, test_jar):
    """
    Parse file which contains several scenarios. Its content looks like the following examples.
    scenarioIndex   classPath scenarioName  jobparam1   jobparams2
    1 org.apache.Test testScenario1 aaa bbb
    ……
    :param scenario_file_name: scenario's file
    :param test_jar:
    :return: list of scenarios
    """
    params_name = []
    scenarios = []
    scenario_names = []
    linenum = 0
    with open(scenario_file_name) as file:
        for data in file:
            if data.startswith("#") or data.startswith(" .*") or data == "":
                continue
            linenum = linenum + 1
            cmd = ""
            scenario_name = ""
            if linenum == 1:
                params_name = data.split(" ")
                if not ("testClassPath" in params_name):
                    return 1, []
            else:
                params_value = data.split(" ")
                for index in range(0, len(params_name)):
                    param = params_name[index]
                    value = params_value[index]
                    if param == "testClassPath":
                        cmd = "-c %s %s %s" % (params_value[index], test_jar,  cmd)
                    else:
                        if param == "":
                            cmd = "--%s %s" % (param, params_value[index])
                        else:
                            cmd = "%s --%s %s" % (cmd, param, params_value[index])
                scenario_name = "%s_%s" % (scenario_name, value)
            scenario_names.append(scenario_name[1:-1])
            scenarios.append(cmd)
    return 0, scenarios, scenario_names


def get_avg(values):
    if len(values) == 0:
        return 0.0
    else:
        return sum(values) * 1.0 / len(values)


def cancel_job(job_id, flink_home, am_seserver_dddress):
    cmd = "%s/bin/flink -m cancel %s %s " % (flink_home, am_seserver_dddress, job_id)
    status, output = run_command(cmd)
    if status:
        return True
    else:
        logger.error("stop server failed:%s" % output)
        return False


def get_job_id(output):
    regex_match = re.search("Job has been submitted with JobID ([a-z0-9]{32})", output)
    job_id = regex_match.group(1)
    return job_id


def run_cases(scenario_file_name, flink_home, am_seserver_dddress, inter_nums=10, wait_minute=10):
    status = start_server(flink_home)
    if not status:
        logger.info("start server failed")
        return 1
    status, scenarios, scenario_names = get_scenarios(scenario_file_name)
    for scenario_index in range(0, len(scenarios)):
        scenario = scenarios.get(scenario_index)
        scenario_name = scenario_names[scenario_index]
        total_qps = []
        for inter_index in range(0, inter_nums):
            cmd = "bash %s/bin/flink run %s" % (flink_home, scenario)
            status, output = run_command(cmd)
            if status:
                job_id = get_job_id(output)
                for qps_index in range(0, 20):
                    qps = get_avg_qps_by_restful_interface(am_seserver_dddress, job_id)
                    total_qps.append(qps)
                    time.sleep(wait_minute)
                cancel_job(job_id, flink_home, am_seserver_dddress)
            else:
                logger.error("status:%s, output:%s" % (status, output))
                return 1
        avg_qps = get_avg(total_qps)
        logger.info("The avg qps of %s's  is %s" % (scenario_name, avg_qps))
    end_server(flink_home)


def usage():
    logger.info("python3 run_case.py scenario_file flink_home am_seserver_dddress inter_nums wait_minute")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("The param's number must be larger than 3")
        usage()
        sys.exit(1)
    am_seserver_dddress = sys.argv[1]
    scenario_file = sys.argv[2]
    flink_home = sys.argv[3]
    if len(sys.argv) > 4:
        inter_nums = sys.argv[4]
    if len(sys.argv) > 5:
        wait_minute = sys.argv[5]

    run_cases(scenario_file, flink_home, am_seserver_dddress, inter_nums=10, wait_minute=10)
