#!/usr/bin/env bash
# set -x
awslocal sqs create-queue --region eu-west-1 --queue-name vibium-analysis-in
awslocal s3 mb s3://vibium-bucket
# set +x
