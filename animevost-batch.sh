#!/bin/sh
awk '{print $1}' animevost-batch_source-2023Q2.csv | uniq > animevost-batch.list
