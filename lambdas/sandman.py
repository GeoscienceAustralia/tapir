#!/usr/bin/python

from __future__ import print_function
import boto3
import datetime

def get_metric(instance, metric):
    """
    Get metric for current instance
    """

    cw_client = boto3.client('cloudwatch')
    mins = 20
    end = datetime.datetime.now().astimezone()
    start = end - datetime.timedelta(minutes=mins)

    datapoints = cw_client.get_metric_statistics(Namespace=metric['namespace'],
                                           MetricName=metric['metricname'],
                                           Dimensions=[
                                               {
                                                   'Name': 'InstanceId',
                                                   'Value': instance
                                               },
                                           ],
                                           StartTime=start,
                                           EndTime=end,
                                           Period=300,
                                           Statistics=['Average'],
                                           Unit='Percent'
                                           )['Datapoints']

    # Get the average from each datapoint that was returned and make an average of those, or set the average to 0.0 if no datapoints were found
    if datapoints:
        total = 0.0

        for data in datapoints:
            total += float(data['Average'])

        average = (total/len(datapoints))
    else:
        average = 0.0

    return average


def check_for_cpu_issues(curr_metric, threshold, average, asg, instance, terminated, test=False):
    """
    This function checks the metric against the provided average, and threshold and terminates the instance if
    the metric is over 90, as well as over 50 above the average.
    """
    testmsg = 'skipping terminate as this has been flagged as a test' if test else ''
    print('-----Average CPU for other instances sharing same autosacaling group: {0}'.format(average))
    diff = curr_metric - average
    print('-----diff = {0}'.format(diff))

    ec2_client = boto3.client('ec2')

    if curr_metric > threshold and diff >= 50 and average != 0.0:
                print('-----{0} average of {1} is above {2}, and at least 50% higher than the average of the rest of '
                      'it\'s autoscaling group {3}, which has an average (excluding this instance) of {4}'
                      .format(instance, curr_metric, threshold, asg, average))
                if not terminated:
                    print('-----Terminating {0}...'.format(instance))
                    ec2_client.terminate_instances(InstanceIds=[instance]) if not test else print(testmsg)
                    return True
    else:
        return False


def lambda_handler(event, context):
    """
    This lambda script is designed to find and terminate the first autoscaled instance
    it finds that is running above a certain level of cpu and memory across a
    certain amount of time.
    """

    asg_client = boto3.client('autoscaling')
    terminated = False
    terminated_instance = None
    autoscaling_groups = {}
    metric = {'namespace': 'AWS/EC2', 'metricname': 'CPUUtilization', 'threshold': 90}

    # Get all autoscaling instances
    autoscaling_instances = asg_client.describe_auto_scaling_instances()['AutoScalingInstances']

    for instance in autoscaling_instances:
        autoscaling_groups.setdefault(instance['AutoScalingGroupName'], []).append(instance['InstanceId'])

    for asg in autoscaling_groups:
        print('Checking ASG: {0}'.format(asg))
        for instance in autoscaling_groups[asg]:
            print('-----Checking instance: {0}'.format(instance))
            other_metrics = []

            curr_metric = get_metric(instance, metric)
            print('-----Average CPU for this instance: {0}'.format(curr_metric))

            for other_instance in autoscaling_groups[asg]:
                if other_instance != instance:
                    other_metrics.append(get_metric(other_instance, metric))

            average = (sum(other_metrics)/len(other_metrics)) if len(other_metrics) > 0 else 0.0

            terminated = check_for_cpu_issues(curr_metric=curr_metric,
                                              threshold=metric['threshold'],
                                              average=average,
                                              asg=asg,
                                              instance=instance,
                                              terminated=terminated)
            if terminated:
                terminated_instance = instance

    if not terminated:
        print('No autoscaled instances found with out of the ordinary cpu levels')
    else:
        print('One instance ({0}) was terminated for having cpu that had significantly spiked above the rest of '
              'its autoscaling group'.format(terminated_instance))
