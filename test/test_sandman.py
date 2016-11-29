#!/usr/bin/python3

from lambdas.sandman import check_for_cpu_issues
from nose.tools import *


def test_single_high_cpu_standout():
    """
    Tests a case where one instance in an autoscaling group is maxing out its cpu (should terminate)
    """
    killed = check_for_cpu_issues(curr_metric=99.99,
                                  threshold=90.0,
                                  average=20.0,
                                  asg='TestASG',
                                  instance='TestInstance',
                                  terminated=False,
                                  test=True)

    assert_equals(killed, True)


def test_multi_high_cpus():
    """
    Tests a case where all instances in an autoscaling group are under high cpu stress (shouldn't terminate)
    """
    killed = check_for_cpu_issues(curr_metric=99.99,
                                  threshold=90.0,
                                  average=80.0,
                                  asg='TestASG',
                                  instance='TestInstance',
                                  terminated=False,
                                  test=True)

    assert_equals(killed, False)


def test_normal_cpu():
    """
    Tests a case where all instances in an autoscaling group are at normal cpu levels (shouldn't terminate)
    """
    killed = check_for_cpu_issues(curr_metric=20.0,
                                  threshold=90.0,
                                  average=20.0,
                                  asg='TestASG',
                                  instance='TestInstance',
                                  terminated=False,
                                  test=True)

    assert_equals(killed, False)


def test_only_one_instance_high_cpu():
    """
    Tests a case where the instance in an autoscaling group of only one instance is under high cpu stress (shouldn't terminate)
    """
    killed = check_for_cpu_issues(curr_metric=99.99,
                                  threshold=90.0,
                                  average=0.0,
                                  asg='TestASG',
                                  instance='TestInstance',
                                  terminated=False,
                                  test=True)

    assert_equals(killed, False)


def test_only_one_instance_normal_cpu():
    """
    Tests a case where the instance in an autoscaling group of only one instance is at normal cpu levels (shouldn't terminate)
    """
    killed = check_for_cpu_issues(curr_metric=20.0,
                                  threshold=90.0,
                                  average=0.0,
                                  asg='TestASG',
                                  instance='TestInstance',
                                  terminated=False,
                                  test=True)

    assert_equals(killed, False)