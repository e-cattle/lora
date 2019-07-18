#!/bin/sh -e

echo "Starting daemon..."

echo "Change to folder $1..."

cd $1

echo "Actual folder:"

pwd

echo "Reseting concentrator..."

./driver/reset_lgw.sh stop
./driver/reset_lgw.sh start

echo "Change to folder $2..."

cd $2

echo "Actual folder:"

pwd

echo "Runnig lora_pkt_fwd..."

lora_pkt_fwd
