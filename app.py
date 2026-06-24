#!/usr/bin/env python3
from aws_cdk import App, Environment
from infrastructure.bedrock_discord_stack import BedrockDiscordStack

app = App()

# Get AWS account and region from environment or use defaults
env = Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "us-west-2"
)

BedrockDiscordStack(
    app,
    "BedrockDiscordStack",
    env=env,
    description="Discord bot infrastructure with Bedrock Agent integration"
)

app.synth()
