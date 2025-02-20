from aws_cdk import (
    core,
    aws_iam as iam,
    aws_cloudfront as cfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_s3 as s3,
    aws_route53 as route53,
    aws_route53_targets,
)
from dataclasses import dataclass

@dataclass
class StaticSiteStackPrpos:
    domain_name: str
    certificate_arn: str

class StaticSiteStack(core.Stack):
    """
    This stack deploys S3 + CloudFront + Route53.
    Static site content is placed in S3 bucket.
    It is attached with CloudFront to enable CDK and HTTPS.
    The domain is registered by Route53.
    """

    def __init__(self, scope: core.App, name: str, props: StaticSiteStackPrpos, **kwargs) -> None:
        super().__init__(scope, name, **kwargs)

        bucket = s3.Bucket(
            self, "SiteContentBucket",
            public_read_access=False,
            # auto_delete_objects=True,
            removal_policy=core.RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
        )

        certificate = acm.Certificate.from_certificate_arn(
            self, "ACMCertificate", props.certificate_arn
        )

        # CloudFront distribution that provies HTTPS
        distribution = cfront.Distribution(
            self, 'SiteDistribution',
            default_behavior=cfront.BehaviorOptions(
                origin=origins.S3Origin(bucket),
                viewer_protocol_policy=cfront.ViewerProtocolPolicy.HTTPS_ONLY
            ),
            domain_names=[props.domain_name],
            certificate=certificate,
            default_root_object="index.html",
            minimum_protocol_version=cfront.SecurityPolicyProtocol.TLS_V1_2016
        )

        route53.ARecord(
            self, 'SiteAliasRecord',
            zone=route53.HostedZone.from_lookup(
                self, 'zone', domain_name=props.domain_name,
            ),
            record_name=props.domain_name,
            target=route53.AddressRecordTarget.from_alias(
                aws_route53_targets.CloudFrontTarget(distribution)
            )
        )

        core.CfnOutput(self, 'BucketName', value=bucket.bucket_name)
