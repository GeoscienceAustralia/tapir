#!/usr/bin/python

from __future__ import print_function
import boto3
import datetime

def lambda_handler(event, context):
    """
    This lambda script is designed to find and terminate the first autoscaled instance
    it finds that is running above a certain level of cpu and memory across a
    certain amount of time.
    """

    # Setup variables to use throughout the script
    asg_client = boto3.client('autoscaling')
    ec2_client = boto3.client('ec2')
    cw_client = boto3.client('cloudwatch')
    mins = 20
    threshold = 90.0
    terminated = False
    end = datetime.datetime.now()
    start = end - datetime.timedelta(minutes=mins)
    instance_ids = []
    metrics = [{'namespace': 'AWS/EC2', 'metricname': 'CPUUtilization'},
               {'namespace': 'System/Linux', 'metricname': 'MemoryUtilization'}]

    # Get all autoscaling instances
    autoscaling_instances = asg_client.describe_auto_scaling_instances()['AutoScalingInstances']

    # Weed out any instances that aren't currently In Service
    for instance in autoscaling_instances:
        if instance['LifecycleState'] == 'InService':
            instance_ids.append(instance['InstanceId'])

    for instance in instance_ids:

        averages = []

        for metric in metrics:
            curr_metric = cw_client.get_metric_statistics(Namespace=metric['namespace'],
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
                                                          )

            datapoints = curr_metric['Datapoints']

            # Get the average from each datapoint that was returned and make an average of those, or set the average to 0.0 if no datapoints were found
            if datapoints:
                total = 0.0
                print('{0} datapoints were returned for metric: {1} on instance: {2}'.format(len(datapoints), metric['metricname'], instance))

                for data in datapoints:
                    total += float(data['Average'])

                average = (total/len(datapoints))
            else:
                average = 0.0

            averages.append(average)

            # Set flags to determine whether to terminate this instance or not
            cpu_terminate = False
            mem_terminate = False
            both_collected = False

            if len(averages) > 1:
                print('got {0} averages for {1}'.format(len(averages), instance))
                both_collected = True

            if both_collected and averages[0] > threshold:
                print('{0} {1} is at {2}'.format(instance, metrics[0]['metricname'], averages[0]))
                cpu_terminate = True

            if both_collected and averages[1] > threshold:
                print('{0} {1} is at {2}'.format(instance, metrics[1]['metricname'], averages[1]))
                mem_terminate = True

            # If an instance has been found that is running high cpu and ram usage and we haven't already terminated an instance...
            if cpu_terminate and mem_terminate and not terminated:
                print('Terminating {0}...'.format(instance))
                ec2_client.terminate_instances(InstanceIds=[instance])
                terminated = True

    if not terminated:
        print('No autoscaled instances found with cpu or ram outside the threshold of {0}'.format(threshold))
    else:
        print('One instance was terminated for having cpu and ram that was measured above the threshold of {0}'.format(threshold))
