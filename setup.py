  
#!/usr/bin/env python3

from setuptools import setup

setup(
    name='lora-driver',
    version='0.0.1',
    packages=['lora-driver'],
    scripts=['bin/lora-driver.py'],
    install_requires=[
        'paho-mqtt',
        'requests',
        'redis'
    ]
) 
