#!/usr/bin/env python3
"""
RISE AWS CDK Application
Infrastructure as Code for RISE Farming Assistant
"""

import aws_cdk as cdk
from stacks.rise_stack import RiseStack

app = cdk.App()

# Deploy RISE infrastructure stack
RiseStack(
    app,
    "RiseStack",
    description="RISE - Rural Innovation and Sustainable Ecosystem Infrastructure",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1"
    )
)

app.synth()
