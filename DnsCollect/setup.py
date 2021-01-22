# -*-coding:utf-8 -*-
from setuptools import setup, find_packages

# requests
setup(
    name="DnsC",
    description=" https Dns search ",
    version="1.0.0",
    author="liulinghong",
    author_email="1285083123@qq.com",
    install_requires=["apscheduler", "elasticsearch","pyyaml"],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            'dns_scheduler=DnsCollect.scheduler:main',
            'dns_output=DnsCollect.output.output:tappscan_assetput',
        ]
    }
)
