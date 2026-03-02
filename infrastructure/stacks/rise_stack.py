"""
RISE Main Infrastructure Stack
Defines all AWS resources for the RISE platform
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class RiseStack(Stack):
    """Main RISE infrastructure stack"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB tables
        self._create_dynamodb_tables()
        
        # Create S3 buckets
        self._create_s3_buckets()
        
        # Create CloudFront distribution
        self._create_cloudfront_distribution()
        
        # Create API Gateway
        self._create_api_gateway()
        
        # Create IAM roles for Bedrock access
        self._create_bedrock_roles()

    def _create_dynamodb_tables(self):
        """Create all DynamoDB tables for RISE"""
        
        # User Profiles Table
        self.user_profiles_table = dynamodb.Table(
            self, "UserProfilesTable",
            table_name="RISE-UserProfiles",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        
        # Add GSIs for User Profiles
        self.user_profiles_table.add_global_secondary_index(
            index_name="PhoneIndex",
            partition_key=dynamodb.Attribute(
                name="phone_number",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.user_profiles_table.add_global_secondary_index(
            index_name="LocationIndex",
            partition_key=dynamodb.Attribute(
                name="location_state",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="location_district",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Farm Data Table
        self.farm_data_table = dynamodb.Table(
            self, "FarmDataTable",
            table_name="RISE-FarmData",
            partition_key=dynamodb.Attribute(
                name="farm_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        
        # Diagnosis History Table
        self.diagnosis_history_table = dynamodb.Table(
            self, "DiagnosisHistoryTable",
            table_name="RISE-DiagnosisHistory",
            partition_key=dynamodb.Attribute(
                name="diagnosis_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        
        # Add GSI for user-based diagnosis retrieval
        self.diagnosis_history_table.add_global_secondary_index(
            index_name="UserDiagnosisIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Resource Sharing Table
        self.resource_sharing_table = dynamodb.Table(
            self, "ResourceSharingTable",
            table_name="RISE-ResourceSharing",
            partition_key=dynamodb.Attribute(
                name="resource_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="availability_date",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        
        # Add GSIs for Resource Sharing
        self.resource_sharing_table.add_global_secondary_index(
            index_name="LocationResourceIndex",
            partition_key=dynamodb.Attribute(
                name="location_state",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="resource_type",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.resource_sharing_table.add_global_secondary_index(
            index_name="OwnerResourceIndex",
            partition_key=dynamodb.Attribute(
                name="owner_user_id",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Buying Groups Table
        self.buying_groups_table = dynamodb.Table(
            self, "BuyingGroupsTable",
            table_name="RISE-BuyingGroups",
            partition_key=dynamodb.Attribute(
                name="group_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        
        # Add GSIs for Buying Groups
        self.buying_groups_table.add_global_secondary_index(
            index_name="LocationGroupIndex",
            partition_key=dynamodb.Attribute(
                name="location_area",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.buying_groups_table.add_global_secondary_index(
            index_name="StatusGroupIndex",
            partition_key=dynamodb.Attribute(
                name="group_status",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Resource Bookings Table
        self.resource_bookings_table = dynamodb.Table(
            self, "ResourceBookingsTable",
            table_name="RISE-ResourceBookings",
            partition_key=dynamodb.Attribute(
                name="booking_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        
        # Add GSIs for Resource Bookings
        self.resource_bookings_table.add_global_secondary_index(
            index_name="RenterBookingIndex",
            partition_key=dynamodb.Attribute(
                name="renter_user_id",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.resource_bookings_table.add_global_secondary_index(
            index_name="OwnerBookingIndex",
            partition_key=dynamodb.Attribute(
                name="owner_user_id",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.resource_bookings_table.add_global_secondary_index(
            index_name="ResourceBookingIndex",
            partition_key=dynamodb.Attribute(
                name="resource_id",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Conversation History Table
        self.conversation_history_table = dynamodb.Table(
            self, "ConversationHistoryTable",
            table_name="RISE-ConversationHistory",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="ttl",  # Enable TTL for automatic cleanup
        )
        
        # Add GSI for user-based conversation retrieval
        self.conversation_history_table.add_global_secondary_index(
            index_name="UserConversationIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Pest Diagnosis History Table
        self.pest_diagnosis_table = dynamodb.Table(
            self, "PestDiagnosisHistoryTable",
            table_name="RISE-PestDiagnosisHistory",
            partition_key=dynamodb.Attribute(
                name="diagnosis_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        
        # Add GSI for user-based pest diagnosis retrieval
        self.pest_diagnosis_table.add_global_secondary_index(
            index_name="UserPestDiagnosisIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Pest Knowledge Base Table
        self.pest_knowledge_table = dynamodb.Table(
            self, "PestKnowledgeBaseTable",
            table_name="RISE-PestKnowledgeBase",
            partition_key=dynamodb.Attribute(
                name="pest_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        
        # Add GSI for pest name search
        self.pest_knowledge_table.add_global_secondary_index(
            index_name="PestNameIndex",
            partition_key=dynamodb.Attribute(
                name="pest_name",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

    def _create_s3_buckets(self):
        """Create S3 buckets with lifecycle policies"""
        
        # Main application data bucket
        self.app_data_bucket = s3.Bucket(
            self, "AppDataBucket",
            bucket_name=f"rise-application-data-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                # Voice queries - delete after 30 days
                s3.LifecycleRule(
                    id="DeleteVoiceQueries",
                    prefix="audio/voice-queries/",
                    expiration=Duration.days(30),
                    enabled=True
                ),
                # Crop images - move to IA after 90 days, Glacier after 1 year
                s3.LifecycleRule(
                    id="ArchiveCropImages",
                    prefix="images/crop-photos/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365)
                        )
                    ],
                    enabled=True
                ),
                # Pest images - move to IA after 90 days, Glacier after 1 year
                s3.LifecycleRule(
                    id="ArchivePestImages",
                    prefix="images/pest-photos/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365)
                        )
                    ],
                    enabled=True
                ),
                # Thumbnails - move to IA after 90 days
                s3.LifecycleRule(
                    id="ArchiveThumbnails",
                    prefix="images/thumbnails/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90)
                        )
                    ],
                    enabled=True
                )
            ],
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=3000
                )
            ]
        )

    def _create_cloudfront_distribution(self):
        """Create CloudFront distribution for content delivery"""
        
        # Create Origin Access Identity for S3
        oai = cloudfront.OriginAccessIdentity(
            self, "RiseOAI",
            comment="OAI for RISE application data"
        )
        
        # Grant read permissions to CloudFront
        self.app_data_bucket.grant_read(oai)
        
        # Create CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self, "RiseDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.app_data_bucket,
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                compress=True
            ),
            additional_behaviors={
                # Static content - long TTL
                "static-content/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.app_data_bucket,
                        origin_access_identity=oai
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy(
                        self, "StaticContentCachePolicy",
                        default_ttl=Duration.days(365),
                        max_ttl=Duration.days(365),
                        min_ttl=Duration.days(1),
                        enable_accept_encoding_gzip=True,
                        enable_accept_encoding_brotli=True
                    )
                ),
                # Images - medium TTL
                "images/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.app_data_bucket,
                        origin_access_identity=oai
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy(
                        self, "ImagesCachePolicy",
                        default_ttl=Duration.days(7),
                        max_ttl=Duration.days(30),
                        min_ttl=Duration.hours(1),
                        enable_accept_encoding_gzip=True,
                        enable_accept_encoding_brotli=True
                    )
                )
            },
            price_class=cloudfront.PriceClass.PRICE_CLASS_200,
            enable_logging=True,
            comment="RISE CDN Distribution"
        )

    def _create_api_gateway(self):
        """Create API Gateway with REST and WebSocket APIs"""
        
        # Create REST API
        self.rest_api = apigateway.RestApi(
            self, "RiseRestApi",
            rest_api_name="RISE-API",
            description="RISE Farming Assistant REST API",
            deploy_options=apigateway.StageOptions(
                stage_name="v1",
                throttling_rate_limit=1000,
                throttling_burst_limit=2000,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                caching_enabled=True,
                cache_ttl=Duration.hours(6)
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["*"]
            )
        )
        
        # Create API resources structure
        api_v1 = self.rest_api.root.add_resource("api").add_resource("v1")
        
        # Auth endpoints
        auth = api_v1.add_resource("auth")
        auth.add_resource("login")
        auth.add_resource("register")
        auth.add_resource("refresh-token")
        
        # Voice endpoints
        voice = api_v1.add_resource("voice")
        voice.add_resource("transcribe")
        voice.add_resource("synthesize")
        voice.add_resource("translate")
        
        # Diagnosis endpoints
        diagnosis = api_v1.add_resource("diagnosis")
        diagnosis.add_resource("crop-disease")
        diagnosis.add_resource("pest-identification")
        diagnosis.add_resource("soil-analysis")
        
        # Intelligence endpoints
        intelligence = api_v1.add_resource("intelligence")
        intelligence.add_resource("weather").add_resource("{location}")
        intelligence.add_resource("market-prices").add_resource("{crop}").add_resource("{location}")
        intelligence.add_resource("schemes").add_resource("{user_id}")
        
        # Community endpoints
        community = api_v1.add_resource("community")
        community.add_resource("forums")
        community.add_resource("discussions")
        community.add_resource("translate-message")
        community.add_resource("resource-sharing")
        community.add_resource("list-equipment")
        community.add_resource("available-equipment").add_resource("{location}")
        community.add_resource("book-equipment")
        community.add_resource("buying-groups")
        community.add_resource("create-buying-group")
        community.add_resource("join-buying-group")
        community.add_resource("resource-alerts").add_resource("{user_id}")
        
        # Financial endpoints
        financial = api_v1.add_resource("financial")
        financial.add_resource("calculate-profitability")
        financial.add_resource("loan-products")
        financial.add_resource("scheme-eligibility")
        
        # Sharing endpoints
        sharing = api_v1.add_resource("sharing")
        sharing.add_resource("equipment-availability")
        sharing.add_resource("equipment-booking")
        sharing.add_resource("cooperative-opportunities")
        sharing.add_resource("bulk-order-creation")
        sharing.add_resource("local-economy-metrics")
        
        # Create WebSocket API
        self.websocket_api = apigateway.CfnApi(
            self, "RiseWebSocketApi",
            name="RISE-WebSocket-API",
            protocol_type="WEBSOCKET",
            route_selection_expression="$request.body.action",
            description="RISE Real-time WebSocket API"
        )
        
        # WebSocket stage
        self.websocket_stage = apigateway.CfnStage(
            self, "RiseWebSocketStage",
            api_id=self.websocket_api.ref,
            stage_name="production",
            auto_deploy=True,
            default_route_settings=apigateway.CfnStage.RouteSettingsProperty(
                throttling_burst_limit=5000,
                throttling_rate_limit=2000
            )
        )

    def _create_bedrock_roles(self):
        """Create IAM roles for Amazon Bedrock access"""
        
        # Create role for Lambda functions to access Bedrock
        self.bedrock_execution_role = iam.Role(
            self, "BedrockExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role for Lambda functions to access Amazon Bedrock",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Add Bedrock permissions
        self.bedrock_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ListFoundationModels",
                    "bedrock:GetFoundationModel"
                ],
                resources=["*"]
            )
        )
        
        # Add permissions for other AWS services
        self.bedrock_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "translate:TranslateText",
                    "transcribe:StartTranscriptionJob",
                    "transcribe:GetTranscriptionJob",
                    "polly:SynthesizeSpeech",
                    "comprehend:DetectDominantLanguage",
                    "comprehend:DetectSentiment"
                ],
                resources=["*"]
            )
        )
        
        # Grant DynamoDB access
        self.user_profiles_table.grant_read_write_data(self.bedrock_execution_role)
        self.farm_data_table.grant_read_write_data(self.bedrock_execution_role)
        self.diagnosis_history_table.grant_read_write_data(self.bedrock_execution_role)
        self.pest_diagnosis_table.grant_read_write_data(self.bedrock_execution_role)
        self.pest_knowledge_table.grant_read_write_data(self.bedrock_execution_role)
        self.resource_sharing_table.grant_read_write_data(self.bedrock_execution_role)
        self.buying_groups_table.grant_read_write_data(self.bedrock_execution_role)
        self.resource_bookings_table.grant_read_write_data(self.bedrock_execution_role)
        self.conversation_history_table.grant_read_write_data(self.bedrock_execution_role)
        
        # Grant S3 access
        self.app_data_bucket.grant_read_write(self.bedrock_execution_role)
