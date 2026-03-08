"""
RISE Main Infrastructure Stack
Defines all AWS resources for the RISE platform
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_apigateway as apigateway,
    aws_apigatewayv2_alpha as apigwv2,
    aws_iam as iam,
    aws_logs as logs,
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
    aws_dax as dax,
)
from constructs import Construct


class RiseStack(Stack):
    """Main RISE infrastructure stack"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC for ElastiCache and DAX
        self._create_vpc()
        
        # Create DynamoDB tables
        self._create_dynamodb_tables()
        
        # Create DynamoDB DAX cluster for hot data
        self._create_dax_cluster()
        
        # Create S3 buckets
        self._create_s3_buckets()
        
        # Create ElastiCache Redis for session management
        self._create_elasticache_redis()
        
        # Create CloudFront distribution with enhanced caching
        self._create_cloudfront_distribution()
        
        # Create API Gateway with caching enabled
        self._create_api_gateway()
        
        # Create IAM roles for Bedrock access
        self._create_bedrock_roles()
        
        # Output important endpoints and configuration
        self._create_outputs()

    def _create_vpc(self):
        """Create VPC for ElastiCache and DAX clusters"""
        
        self.vpc = ec2.Vpc(
            self, "RiseVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )
        
        # Security group for ElastiCache
        self.redis_security_group = ec2.SecurityGroup(
            self, "RedisSecurityGroup",
            vpc=self.vpc,
            description="Security group for ElastiCache Redis",
            allow_all_outbound=True
        )
        
        # Allow Redis port from within VPC
        self.redis_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(6379),
            description="Allow Redis access from VPC"
        )
        
        # Security group for DAX
        self.dax_security_group = ec2.SecurityGroup(
            self, "DaxSecurityGroup",
            vpc=self.vpc,
            description="Security group for DynamoDB DAX",
            allow_all_outbound=True
        )
        
        # Allow DAX port from within VPC
        self.dax_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(8111),
            description="Allow DAX access from VPC"
        )

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
        
        # Forum Posts Table (Farmer Forum)
        self.forum_posts_table = dynamodb.Table(
            self, "ForumPostsTable",
            table_name="RISE-ForumPosts",
            partition_key=dynamodb.Attribute(
                name="post_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        self.forum_posts_table.add_global_secondary_index(
            index_name="UserPostsIndex",
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
        
        # Weather Forecast Table
        self.weather_forecast_table = dynamodb.Table(
            self, "WeatherForecastTable",
            table_name="RISE-WeatherForecast",
            partition_key=dynamodb.Attribute(
                name="cache_key",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="ttl",  # Enable TTL for automatic cache cleanup
        )
        
        # Market Prices Table
        self.market_prices_table = dynamodb.Table(
            self, "MarketPricesTable",
            table_name="RISE-MarketPrices",
            partition_key=dynamodb.Attribute(
                name="crop_market_id",
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
            time_to_live_attribute="ttl",  # Enable TTL for automatic data cleanup
        )
        
        # Add GSI for cache lookups
        self.market_prices_table.add_global_secondary_index(
            index_name="CacheKeyIndex",
            partition_key=dynamodb.Attribute(
                name="cache_key",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Government Schemes Table
        self.government_schemes_table = dynamodb.Table(
            self, "GovernmentSchemesTable",
            table_name="RISE-GovernmentSchemes",
            partition_key=dynamodb.Attribute(
                name="scheme_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        
        # Add GSIs for Government Schemes
        self.government_schemes_table.add_global_secondary_index(
            index_name="StateSchemeIndex",
            partition_key=dynamodb.Attribute(
                name="state",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="scheme_type",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.government_schemes_table.add_global_secondary_index(
            index_name="CategorySchemeIndex",
            partition_key=dynamodb.Attribute(
                name="category",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="benefit_amount",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        self.government_schemes_table.add_global_secondary_index(
            index_name="DeadlineSchemeIndex",
            partition_key=dynamodb.Attribute(
                name="active_status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="application_deadline",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Supplier Negotiation Tables (AI-Powered Supplier Negotiation)
        self.suppliers_table = dynamodb.Table(
            self, "SuppliersTable",
            table_name="RISE-Suppliers",
            partition_key=dynamodb.Attribute(
                name="supplier_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        self.negotiations_table = dynamodb.Table(
            self, "NegotiationsTable",
            table_name="RISE-Negotiations",
            partition_key=dynamodb.Attribute(
                name="negotiation_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        self.supplier_quotes_table = dynamodb.Table(
            self, "SupplierQuotesTable",
            table_name="RISE-SupplierQuotes",
            partition_key=dynamodb.Attribute(
                name="quote_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        # Best Practices Library tables
        self.best_practices_table = dynamodb.Table(
            self, "BestPracticesTable",
            table_name="RISE-BestPractices",
            partition_key=dynamodb.Attribute(
                name="practice_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )
        self.practice_adoptions_table = dynamodb.Table(
            self, "PracticeAdoptionsTable",
            table_name="RISE-PracticeAdoptions",
            partition_key=dynamodb.Attribute(
                name="adoption_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

    def _create_dax_cluster(self):
        """Create DynamoDB DAX cluster for microsecond latency on hot data"""
        
        # Create IAM role for DAX
        self.dax_role = iam.Role(
            self, "DaxServiceRole",
            assumed_by=iam.ServicePrincipal("dax.amazonaws.com"),
            description="Service role for DynamoDB DAX cluster"
        )
        
        # Grant DAX access to DynamoDB tables (read-only for caching)
        self.user_profiles_table.grant_read_data(self.dax_role)
        self.farm_data_table.grant_read_data(self.dax_role)
        self.diagnosis_history_table.grant_read_data(self.dax_role)
        self.weather_forecast_table.grant_read_data(self.dax_role)
        self.market_prices_table.grant_read_data(self.dax_role)
        self.government_schemes_table.grant_read_data(self.dax_role)
        
        # Create subnet group for DAX
        self.dax_subnet_group = dax.CfnSubnetGroup(
            self, "DaxSubnetGroup",
            subnet_group_name="rise-dax-subnet-group",
            description="Subnet group for RISE DAX cluster",
            subnet_ids=[subnet.subnet_id for subnet in self.vpc.private_subnets]
        )
        
        # Create DAX cluster
        self.dax_cluster = dax.CfnCluster(
            self, "DaxCluster",
            cluster_name="rise-dax-cluster",
            iam_role_arn=self.dax_role.role_arn,
            node_type="dax.t3.small",
            replication_factor=2,  # 1 primary + 1 replica for HA
            subnet_group_name=self.dax_subnet_group.subnet_group_name,
            security_group_ids=[self.dax_security_group.security_group_id],
            description="DAX cluster for RISE hot data caching",
            sse_specification=dax.CfnCluster.SSESpecificationProperty(
                sse_enabled=True
            )
        )
        
        self.dax_cluster.add_dependency(self.dax_subnet_group)

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

    def _create_elasticache_redis(self):
        """Create ElastiCache Redis cluster for session management and application caching"""
        
        # Create subnet group for ElastiCache
        self.redis_subnet_group = elasticache.CfnSubnetGroup(
            self, "RedisSubnetGroup",
            description="Subnet group for RISE Redis cluster",
            subnet_ids=[subnet.subnet_id for subnet in self.vpc.private_subnets],
            cache_subnet_group_name="rise-redis-subnet-group"
        )
        
        # Create Redis replication group (cluster mode disabled for simplicity)
        self.redis_cluster = elasticache.CfnReplicationGroup(
            self, "RedisCluster",
            replication_group_id="rise-redis-cluster",
            replication_group_description="Redis cluster for RISE session and application caching",
            engine="redis",
            engine_version="7.0",
            cache_node_type="cache.t3.micro",
            num_cache_clusters=2,  # 1 primary + 1 replica
            automatic_failover_enabled=True,
            multi_az_enabled=True,
            cache_subnet_group_name=self.redis_subnet_group.cache_subnet_group_name,
            security_group_ids=[self.redis_security_group.security_group_id],
            at_rest_encryption_enabled=True,
            transit_encryption_enabled=True,
            snapshot_retention_limit=5,
            snapshot_window="03:00-05:00",
            preferred_maintenance_window="sun:05:00-sun:07:00",
            auto_minor_version_upgrade=True
        )
        
        self.redis_cluster.add_dependency(self.redis_subnet_group)

    def _create_cloudfront_distribution(self):
        """Create CloudFront distribution with enhanced caching for static content"""
        
        # Create Origin Access Identity for S3
        oai = cloudfront.OriginAccessIdentity(
            self, "RiseOAI",
            comment="OAI for RISE application data"
        )
        
        # Grant read permissions to CloudFront
        self.app_data_bucket.grant_read(oai)
        
        # Create custom cache policies for different content types
        
        # Static content cache policy - 1 year TTL
        static_cache_policy = cloudfront.CachePolicy(
            self, "StaticContentCachePolicy",
            cache_policy_name="RiseStaticContentPolicy",
            comment="Cache policy for static content with 1 year TTL",
            default_ttl=Duration.days(365),
            max_ttl=Duration.days(365),
            min_ttl=Duration.days(1),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True,
            header_behavior=cloudfront.CacheHeaderBehavior.none(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            cookie_behavior=cloudfront.CacheCookieBehavior.none()
        )
        
        # Images cache policy - 7 days TTL
        images_cache_policy = cloudfront.CachePolicy(
            self, "ImagesCachePolicy",
            cache_policy_name="RiseImagesPolicy",
            comment="Cache policy for images with 7 days TTL",
            default_ttl=Duration.days(7),
            max_ttl=Duration.days(30),
            min_ttl=Duration.hours(1),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True,
            header_behavior=cloudfront.CacheHeaderBehavior.allow_list("Accept"),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            cookie_behavior=cloudfront.CacheCookieBehavior.none()
        )
        
        # Documents cache policy - 1 day TTL
        documents_cache_policy = cloudfront.CachePolicy(
            self, "DocumentsCachePolicy",
            cache_policy_name="RiseDocumentsPolicy",
            comment="Cache policy for documents with 1 day TTL",
            default_ttl=Duration.days(1),
            max_ttl=Duration.days(7),
            min_ttl=Duration.hours(1),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True
        )
        
        # Create CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self, "RiseDistribution",
            comment="RISE CDN Distribution with optimized caching",
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
                # Static content - 1 year TTL for JS, CSS, fonts
                "static-content/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.app_data_bucket,
                        origin_access_identity=oai
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_cache_policy,
                    compress=True
                ),
                # Images - 7 days TTL
                "images/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.app_data_bucket,
                        origin_access_identity=oai
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=images_cache_policy,
                    compress=True
                ),
                # Documents - 1 day TTL
                "documents/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.app_data_bucket,
                        origin_access_identity=oai
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=documents_cache_policy,
                    compress=True
                )
            },
            price_class=cloudfront.PriceClass.PRICE_CLASS_200,
            enable_logging=True,
            http_version=cloudfront.HttpVersion.HTTP2_AND_3,
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021
        )

    def _create_api_gateway(self):
        """Create API Gateway with caching enabled for weather and market data"""
        
        # Create REST API with caching enabled
        self.rest_api = apigateway.RestApi(
            self, "RiseRestApi",
            rest_api_name="RISE-API",
            description="RISE Farming Assistant REST API with caching",
            deploy_options=apigateway.StageOptions(
                stage_name="v1",
                throttling_rate_limit=1000,
                throttling_burst_limit=2000,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                # Enable caching (API Gateway max TTL is 3600 seconds)
                caching_enabled=True,
                cache_ttl=Duration.seconds(3600),
                cache_cluster_enabled=True,
                cache_cluster_size="0.5"  # 0.5 GB cache
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
        self.websocket_api = apigwv2.WebSocketApi(
            self, "RiseWebSocketApi",
            api_name="RISE-WebSocket-API",
            route_selection_expression="$request.body.action",
            description="RISE Real-time WebSocket API"
        )
        
        # WebSocket stage
        self.websocket_stage = apigwv2.WebSocketStage(
            self, "RiseWebSocketStage",
            web_socket_api=self.websocket_api,
            stage_name="production",
            auto_deploy=True
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
        self.weather_forecast_table.grant_read_write_data(self.bedrock_execution_role)
        self.market_prices_table.grant_read_write_data(self.bedrock_execution_role)
        self.government_schemes_table.grant_read_write_data(self.bedrock_execution_role)
        
        # Grant S3 access
        self.app_data_bucket.grant_read_write(self.bedrock_execution_role)

    def _create_outputs(self):
        """Create CloudFormation outputs for important endpoints and configuration"""
        
        # CloudFront distribution URL
        CfnOutput(
            self, "CloudFrontDistributionURL",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="CloudFront distribution URL for static content delivery",
            export_name="RiseCloudFrontURL"
        )
        
        # API Gateway endpoint
        CfnOutput(
            self, "ApiGatewayEndpoint",
            value=self.rest_api.url,
            description="API Gateway REST API endpoint",
            export_name="RiseApiEndpoint"
        )
        
        # Redis cluster endpoint
        CfnOutput(
            self, "RedisClusterEndpoint",
            value=self.redis_cluster.attr_primary_end_point_address,
            description="ElastiCache Redis cluster primary endpoint",
            export_name="RiseRedisEndpoint"
        )
        
        # Redis cluster port
        CfnOutput(
            self, "RedisClusterPort",
            value=self.redis_cluster.attr_primary_end_point_port,
            description="ElastiCache Redis cluster port",
            export_name="RiseRedisPort"
        )
        
        # DAX cluster endpoint
        CfnOutput(
            self, "DaxClusterEndpoint",
            value=self.dax_cluster.attr_cluster_discovery_endpoint,
            description="DynamoDB DAX cluster discovery endpoint",
            export_name="RiseDaxEndpoint"
        )
        
        # S3 bucket name
        CfnOutput(
            self, "S3BucketName",
            value=self.app_data_bucket.bucket_name,
            description="S3 bucket for application data",
            export_name="RiseS3Bucket"
        )
        
        # VPC ID
        CfnOutput(
            self, "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID for ElastiCache and DAX",
            export_name="RiseVpcId"
        )
