from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class BedrockDiscordStack(Stack):
    """
    CDK Stack for Discord bot with Bedrock Agent integration.

    Creates:
    - Lambda function to process Discord messages
    - IAM role with Bedrock Agent permissions
    - CloudWatch log group
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Configuration
        agent_id = "JLD5FDHXV6"
        agent_alias_id = "TSTALIASID"  # Use test alias, or create a specific alias

        # Create IAM role for Lambda
        lambda_role = iam.Role(
            self,
            "MessageProcessorRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role for Discord message processor Lambda",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Grant Bedrock Agent permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeAgent",
                    "bedrock:InvokeModel",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:agent/{agent_id}",
                    f"arn:aws:bedrock:{self.region}:{self.account}:agent-alias/{agent_id}/*",
                ]
            )
        )

        # Grant access to retrieve agent details
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:GetAgent",
                    "bedrock:GetAgentAlias",
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:agent/{agent_id}",
                    f"arn:aws:bedrock:{self.region}:{self.account}:agent-alias/{agent_id}/*",
                ]
            )
        )

        # Create Lambda function
        message_processor = lambda_.Function(
            self,
            "MessageProcessor",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="message_processor.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                "BEDROCK_AGENT_ID": agent_id,
                "BEDROCK_AGENT_ALIAS_ID": agent_alias_id,
                "LOG_LEVEL": "INFO",
            },
            description="Processes Discord messages and invokes Bedrock Agent",
        )

        # Outputs
        CfnOutput(
            self,
            "LambdaFunctionName",
            value=message_processor.function_name,
            description="Name of the message processor Lambda function"
        )

        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=message_processor.function_arn,
            description="ARN of the message processor Lambda function"
        )

        CfnOutput(
            self,
            "BedrockAgentId",
            value=agent_id,
            description="ID of the Bedrock Agent"
        )
