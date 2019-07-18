#!/bin/sh -e

echo "Starting daemon..."

FOLDER="$1/bin"

echo "Change to folder $FOLDER..."

cd $FOLDER

echo "Actual folder:"

pwd

echo "Runnig lora_pkt_fwd..."

./lora_pkt_fwd
