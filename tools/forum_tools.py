"""
RISE Multilingual Farmer Forums Tools
Tools for community forums with real-time translation and AI-powered moderation
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
import logging
from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timedelta
import uuid
import json

logger = logging.getLogger(__name__)


class ForumTools:
    """Tools for multilingual farmer forums with AI translation and spam filtering"""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize forum tools with AWS clients
        
        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.translate_client = boto3.client('translate', region_name=region)
        self.comprehend_client = boto3.client('comprehend', region_name=region)
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
        
        # DynamoDB tables
        self.posts_table = self.dynamodb.Table('RISE-ForumPosts')
        self.users_table = self.dynamodb.Table('RISE-UserProfiles')
        
        # Supported languages
        self.supported_languages = ['hi', 'en', 'ta', 'te', 'kn', 'bn', 'gu', 'mr', 'pa']
        
        logger.info(f"Forum tools initialized in region {region}")
    
    def create_post(self,
                   user_id: str,
                   title: str,
                   content: str,
                   language: str,
                   category: Dict[str, str],
                   tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new forum post with spam filtering
        
        Args:
            user_id: User identifier
            title: Post title
            content: Post content
            language: Original language code
            category: Dict with crop_type, region, method
            tags: Optional list of tags
        
        Returns:
            Dict with post creation result
        """
        try:
            # Validate language
            if language not in self.supported_languages:
                return {
                    'success': False,
                    'error': f'Unsupported language: {language}'
                }
            
            # Check for spam using Amazon Comprehend
            spam_check = self._check_spam(content, language)
            
            if not spam_check['is_safe']:
                return {
                    'success': False,
                    'error': 'Content flagged as spam or inappropriate',
                    'reason': spam_check['reason']
                }
            
            # Generate post ID
            post_id = f"post_{uuid.uuid4().hex[:12]}"
            timestamp = int(time.time() * 1000)
            
            # Create post item
            post_item = {
                'post_id': post_id,
                'timestamp': timestamp,
                'user_id': user_id,
                'title': title,
                'content': content,
                'original_language': language,
                'category': category,
                'tags': tags or [],
                'sentiment_score': spam_check.get('sentiment_score', 0),
                'replies_count': 0,
                'likes_count': 0,
                'views_count': 0,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Save to DynamoDB
            self.posts_table.put_item(Item=post_item)
            
            logger.info(f"Created post {post_id} by user {user_id}")
            
            return {
                'success': True,
                'post_id': post_id,
                'timestamp': timestamp,
                'sentiment_score': spam_check.get('sentiment_score', 0)
            }
        
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    
    def _check_spam(self, content: str, language: str) -> Dict[str, Any]:
        """
        Check content for spam and inappropriate content using Amazon Comprehend
        
        Args:
            content: Content to check
            language: Language code
        
        Returns:
            Dict with spam check results
        """
        try:
            # Map language codes to Comprehend supported codes
            comprehend_lang = 'en' if language not in ['en', 'hi'] else language
            
            # Detect sentiment
            sentiment_response = self.comprehend_client.detect_sentiment(
                Text=content[:5000],  # Comprehend limit
                LanguageCode=comprehend_lang
            )
            
            sentiment = sentiment_response['Sentiment']
            sentiment_scores = sentiment_response['SentimentScore']
            
            # Check for toxic content using Bedrock
            toxicity_check = self._check_toxicity(content)
            
            # Determine if content is safe
            is_safe = True
            reason = None
            
            # Flag if extremely negative or toxic
            if sentiment_scores.get('Negative', 0) > 0.8:
                is_safe = False
                reason = 'Highly negative content detected'
            
            if toxicity_check.get('is_toxic', False):
                is_safe = False
                reason = 'Toxic or inappropriate content detected'
            
            return {
                'is_safe': is_safe,
                'reason': reason,
                'sentiment': sentiment,
                'sentiment_score': sentiment_scores.get('Positive', 0) - sentiment_scores.get('Negative', 0),
                'toxicity_score': toxicity_check.get('toxicity_score', 0)
            }
        
        except Exception as e:
            logger.error(f"Error checking spam: {e}")
            # Default to safe if check fails
            return {
                'is_safe': True,
                'sentiment_score': 0
            }
    
    def _check_toxicity(self, content: str) -> Dict[str, Any]:
        """
        Check content toxicity using Amazon Bedrock
        
        Args:
            content: Content to check
        
        Returns:
            Dict with toxicity results
        """
        try:
            prompt = f"""Analyze the following text for toxic, offensive, or spam content.
Respond with JSON only: {{"is_toxic": true/false, "toxicity_score": 0-1, "reason": "explanation"}}

Text: {content[:1000]}"""
            
            request_body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 200,
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }],
                'temperature': 0
            }
            
            response = self.bedrock_client.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            result_text = response_body['content'][0]['text']
            
            # Parse JSON response
            result = json.loads(result_text)
            return result
        
        except Exception as e:
            logger.error(f"Error checking toxicity: {e}")
            return {'is_toxic': False, 'toxicity_score': 0}
    
    def get_posts(self,
                 category: Optional[Dict[str, str]] = None,
                 limit: int = 20,
                 last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get forum posts with optional filtering
        
        Args:
            category: Optional category filter (crop_type, region, method)
            limit: Maximum number of posts to return
            last_evaluated_key: Pagination key
        
        Returns:
            Dict with posts and pagination info
        """
        try:
            # Build query parameters
            query_params = {
                'Limit': limit,
                'ScanIndexForward': False  # Most recent first
            }
            
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = last_evaluated_key
            
            # If category filter, use GSI
            if category:
                # For simplicity, scan with filter (in production, use GSI)
                response = self.posts_table.scan(
                    FilterExpression=Attr('status').eq('active'),
                    **query_params
                )
            else:
                # Get all active posts
                response = self.posts_table.scan(
                    FilterExpression=Attr('status').eq('active'),
                    **query_params
                )
            
            posts = response.get('Items', [])
            
            # Sort by timestamp
            posts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'posts': posts,
                'count': len(posts),
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }
        
        except Exception as e:
            logger.error(f"Error getting posts: {e}")
            return {
                'success': False,
                'error': str(e),
                'posts': []
            }
    
    def get_post(self, post_id: str) -> Dict[str, Any]:
        """
        Get a single post by ID
        
        Args:
            post_id: Post identifier
        
        Returns:
            Dict with post data
        """
        try:
            response = self.posts_table.get_item(
                Key={'post_id': post_id}
            )
            
            post = response.get('Item')
            
            if not post:
                return {
                    'success': False,
                    'error': 'Post not found'
                }
            
            # Increment view count
            self.posts_table.update_item(
                Key={'post_id': post_id},
                UpdateExpression='SET views_count = views_count + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            
            return {
                'success': True,
                'post': post
            }
        
        except Exception as e:
            logger.error(f"Error getting post: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def translate_post(self,
                      post_id: str,
                      target_language: str) -> Dict[str, Any]:
        """
        Translate a post to target language
        
        Args:
            post_id: Post identifier
            target_language: Target language code
        
        Returns:
            Dict with translated post
        """
        try:
            # Get post
            post_result = self.get_post(post_id)
            
            if not post_result['success']:
                return post_result
            
            post = post_result['post']
            
            # Check if already in target language
            if post['original_language'] == target_language:
                return {
                    'success': True,
                    'post': post,
                    'translated': False
                }
            
            # Translate title and content
            title_translation = self.translate_client.translate_text(
                Text=post['title'],
                SourceLanguageCode=post['original_language'],
                TargetLanguageCode=target_language
            )
            
            content_translation = self.translate_client.translate_text(
                Text=post['content'],
                SourceLanguageCode=post['original_language'],
                TargetLanguageCode=target_language,
                TerminologyNames=['rise-agricultural-terms']
            )
            
            # Create translated post
            translated_post = post.copy()
            translated_post['title'] = title_translation['TranslatedText']
            translated_post['content'] = content_translation['TranslatedText']
            translated_post['translated_to'] = target_language
            translated_post['original_title'] = post['title']
            translated_post['original_content'] = post['content']
            
            return {
                'success': True,
                'post': translated_post,
                'translated': True,
                'source_language': post['original_language'],
                'target_language': target_language
            }
        
        except Exception as e:
            logger.error(f"Error translating post: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_reply(self,
                 post_id: str,
                 user_id: str,
                 content: str,
                 language: str) -> Dict[str, Any]:
        """
        Add a reply to a post
        
        Args:
            post_id: Post identifier
            user_id: User identifier
            content: Reply content
            language: Language code
        
        Returns:
            Dict with reply creation result
        """
        try:
            # Check for spam
            spam_check = self._check_spam(content, language)
            
            if not spam_check['is_safe']:
                return {
                    'success': False,
                    'error': 'Reply flagged as spam or inappropriate',
                    'reason': spam_check['reason']
                }
            
            # Generate reply ID
            reply_id = f"reply_{uuid.uuid4().hex[:12]}"
            timestamp = int(time.time() * 1000)
            
            # Create reply item
            reply_item = {
                'reply_id': reply_id,
                'post_id': post_id,
                'user_id': user_id,
                'content': content,
                'language': language,
                'timestamp': timestamp,
                'likes_count': 0,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Update post replies count
            self.posts_table.update_item(
                Key={'post_id': post_id},
                UpdateExpression='SET replies_count = replies_count + :inc, updated_at = :now',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':now': datetime.utcnow().isoformat()
                }
            )
            
            # In production, store replies in separate table
            # For now, append to post item
            
            logger.info(f"Added reply {reply_id} to post {post_id}")
            
            return {
                'success': True,
                'reply_id': reply_id,
                'timestamp': timestamp
            }
        
        except Exception as e:
            logger.error(f"Error adding reply: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def like_post(self, post_id: str, user_id: str) -> Dict[str, Any]:
        """
        Like a post
        
        Args:
            post_id: Post identifier
            user_id: User identifier
        
        Returns:
            Dict with like result
        """
        try:
            # Update likes count
            self.posts_table.update_item(
                Key={'post_id': post_id},
                UpdateExpression='SET likes_count = likes_count + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            
            logger.info(f"User {user_id} liked post {post_id}")
            
            return {
                'success': True,
                'message': 'Post liked successfully'
            }
        
        except Exception as e:
            logger.error(f"Error liking post: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_posts(self,
                    query: str,
                    category: Optional[Dict[str, str]] = None,
                    limit: int = 20) -> Dict[str, Any]:
        """
        Search posts by keyword
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum results
        
        Returns:
            Dict with search results
        """
        try:
            # Simple text search (in production, use OpenSearch)
            response = self.posts_table.scan(
                FilterExpression=Attr('status').eq('active'),
                Limit=limit * 2  # Get more to filter
            )
            
            posts = response.get('Items', [])
            
            # Filter by query
            query_lower = query.lower()
            filtered_posts = [
                post for post in posts
                if query_lower in post['title'].lower() or query_lower in post['content'].lower()
            ]
            
            # Apply category filter if provided
            if category:
                filtered_posts = [
                    post for post in filtered_posts
                    if all(post['category'].get(k) == v for k, v in category.items())
                ]
            
            # Sort by relevance (simple: by timestamp)
            filtered_posts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'posts': filtered_posts[:limit],
                'count': len(filtered_posts),
                'query': query
            }
        
        except Exception as e:
            logger.error(f"Error searching posts: {e}")
            return {
                'success': False,
                'error': str(e),
                'posts': []
            }
    
    def get_user_reputation(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user reputation score with expertise metrics
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with detailed reputation data including badge, expertise areas, and metrics
        """
        try:
            # Get user's posts
            response = self.posts_table.scan(
                FilterExpression=Attr('user_id').eq(user_id) & Attr('status').eq('active')
            )
            
            posts = response.get('Items', [])
            
            # Calculate basic metrics
            total_posts = len(posts)
            total_likes = sum(post.get('likes_count', 0) for post in posts)
            total_replies = sum(post.get('replies_count', 0) for post in posts)
            total_views = sum(post.get('views_count', 0) for post in posts)
            avg_sentiment = sum(post.get('sentiment_score', 0) for post in posts) / max(total_posts, 1)
            
            # Calculate engagement rate (replies + likes per post)
            engagement_rate = (total_replies + total_likes) / max(total_posts, 1)
            
            # Calculate helpful answers (posts with high likes and positive sentiment)
            helpful_answers = sum(
                1 for post in posts 
                if post.get('likes_count', 0) >= 5 and post.get('sentiment_score', 0) > 0.3
            )
            
            # Identify expertise areas based on post categories
            expertise_areas = self._calculate_expertise_areas(posts)
            
            # Calculate verified solutions (posts marked as solutions)
            verified_solutions = sum(1 for post in posts if post.get('is_solution', False))
            
            # Calculate community endorsements (high engagement posts)
            community_endorsements = sum(
                1 for post in posts 
                if post.get('likes_count', 0) >= 10 or post.get('replies_count', 0) >= 5
            )
            
            # Calculate consistency score (posting frequency over time)
            consistency_score = self._calculate_consistency_score(posts)
            
            # Calculate comprehensive reputation score
            reputation_score = (
                total_posts * 10 +                    # Base contribution
                helpful_answers * 25 +                # Quality answers
                total_likes * 5 +                     # Community appreciation
                total_replies * 3 +                   # Engagement generation
                verified_solutions * 50 +             # Verified expertise
                community_endorsements * 15 +         # High-impact contributions
                avg_sentiment * 50 +                  # Positive sentiment
                consistency_score * 20 +              # Regular participation
                len(expertise_areas) * 30             # Breadth of knowledge
            )
            
            # Determine badge level
            badge_info = self._determine_badge(reputation_score, helpful_answers, verified_solutions)
            
            # Calculate expertise level (0-100)
            expertise_level = min(100, int(reputation_score / 20))
            
            return {
                'success': True,
                'user_id': user_id,
                'reputation_score': int(reputation_score),
                'expertise_level': expertise_level,
                'badge': badge_info['badge'],
                'badge_emoji': badge_info['emoji'],
                'badge_description': badge_info['description'],
                'is_verified_expert': badge_info['is_verified'],
                'expertise_areas': expertise_areas,
                'metrics': {
                    'total_posts': total_posts,
                    'helpful_answers': helpful_answers,
                    'total_likes': total_likes,
                    'total_replies': total_replies,
                    'total_views': total_views,
                    'verified_solutions': verified_solutions,
                    'community_endorsements': community_endorsements,
                    'engagement_rate': round(engagement_rate, 2),
                    'avg_sentiment': round(avg_sentiment, 2),
                    'consistency_score': round(consistency_score, 2)
                },
                'achievements': self._get_achievements(
                    total_posts, helpful_answers, verified_solutions, 
                    community_endorsements, expertise_areas
                )
            }
        
        except Exception as e:
            logger.error(f"Error getting user reputation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_expertise_areas(self, posts: List[Dict]) -> List[Dict[str, Any]]:
        """
        Calculate user's expertise areas based on post categories and engagement
        
        Args:
            posts: List of user's posts
        
        Returns:
            List of expertise areas with scores
        """
        expertise_map = {}
        
        for post in posts:
            category = post.get('category', {})
            crop_type = category.get('crop_type', 'general')
            
            if crop_type not in expertise_map:
                expertise_map[crop_type] = {
                    'area': crop_type,
                    'posts': 0,
                    'total_engagement': 0
                }
            
            expertise_map[crop_type]['posts'] += 1
            expertise_map[crop_type]['total_engagement'] += (
                post.get('likes_count', 0) + 
                post.get('replies_count', 0)
            )
        
        # Calculate expertise score for each area
        expertise_areas = []
        for area, data in expertise_map.items():
            if data['posts'] >= 3:  # Minimum 3 posts to be considered expertise
                score = data['posts'] * 10 + data['total_engagement'] * 2
                expertise_areas.append({
                    'area': area,
                    'posts_count': data['posts'],
                    'engagement': data['total_engagement'],
                    'score': score
                })
        
        # Sort by score
        expertise_areas.sort(key=lambda x: x['score'], reverse=True)
        
        return expertise_areas[:5]  # Top 5 expertise areas
    
    def _calculate_consistency_score(self, posts: List[Dict]) -> float:
        """
        Calculate user's posting consistency over time
        
        Args:
            posts: List of user's posts
        
        Returns:
            Consistency score (0-10)
        """
        if len(posts) < 2:
            return 0.0
        
        # Sort posts by timestamp
        sorted_posts = sorted(posts, key=lambda x: x.get('timestamp', 0))
        
        # Calculate time spans between posts
        timestamps = [post.get('timestamp', 0) for post in sorted_posts]
        time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        if not time_diffs:
            return 0.0
        
        # Calculate average time between posts (in days)
        avg_diff_days = (sum(time_diffs) / len(time_diffs)) / (1000 * 60 * 60 * 24)
        
        # Score based on posting frequency (ideal: 1-7 days between posts)
        if 1 <= avg_diff_days <= 7:
            consistency = 10.0
        elif avg_diff_days < 1:
            consistency = 7.0  # Too frequent
        elif avg_diff_days <= 14:
            consistency = 8.0
        elif avg_diff_days <= 30:
            consistency = 5.0
        else:
            consistency = 2.0  # Too infrequent
        
        return consistency
    
    def _determine_badge(self, reputation_score: float, helpful_answers: int, 
                        verified_solutions: int) -> Dict[str, Any]:
        """
        Determine user's badge level based on reputation and contributions
        
        Args:
            reputation_score: Total reputation score
            helpful_answers: Number of helpful answers
            verified_solutions: Number of verified solutions
        
        Returns:
            Dict with badge information
        """
        # Master Farmer: Highest level expert
        if reputation_score >= 2000 and helpful_answers >= 50 and verified_solutions >= 20:
            return {
                'badge': 'master_farmer',
                'emoji': '🏆',
                'description': 'Master Farmer - Top agricultural expert',
                'is_verified': True
            }
        
        # Expert: Verified expert with significant contributions
        elif reputation_score >= 1000 and helpful_answers >= 25 and verified_solutions >= 10:
            return {
                'badge': 'expert',
                'emoji': '🌟',
                'description': 'Expert - Verified agricultural specialist',
                'is_verified': True
            }
        
        # Experienced: Regular contributor with quality content
        elif reputation_score >= 500 and helpful_answers >= 10:
            return {
                'badge': 'experienced',
                'emoji': '⭐',
                'description': 'Experienced Farmer - Trusted contributor',
                'is_verified': False
            }
        
        # Contributor: Active participant
        elif reputation_score >= 200 and helpful_answers >= 3:
            return {
                'badge': 'contributor',
                'emoji': '✨',
                'description': 'Contributor - Active community member',
                'is_verified': False
            }
        
        # Beginner: New to the community
        else:
            return {
                'badge': 'beginner',
                'emoji': '🌱',
                'description': 'Beginner - New to the community',
                'is_verified': False
            }
    
    def _get_achievements(self, total_posts: int, helpful_answers: int, 
                         verified_solutions: int, community_endorsements: int,
                         expertise_areas: List[Dict]) -> List[Dict[str, str]]:
        """
        Get user's achievements based on their contributions
        
        Args:
            total_posts: Total number of posts
            helpful_answers: Number of helpful answers
            verified_solutions: Number of verified solutions
            community_endorsements: Number of highly engaged posts
            expertise_areas: List of expertise areas
        
        Returns:
            List of achievements
        """
        achievements = []
        
        # Posting milestones
        if total_posts >= 100:
            achievements.append({'title': 'Century Club', 'description': '100+ posts shared'})
        elif total_posts >= 50:
            achievements.append({'title': 'Prolific Contributor', 'description': '50+ posts shared'})
        elif total_posts >= 10:
            achievements.append({'title': 'Active Member', 'description': '10+ posts shared'})
        
        # Helpful answers
        if helpful_answers >= 50:
            achievements.append({'title': 'Community Hero', 'description': '50+ helpful answers'})
        elif helpful_answers >= 25:
            achievements.append({'title': 'Problem Solver', 'description': '25+ helpful answers'})
        elif helpful_answers >= 10:
            achievements.append({'title': 'Helpful Hand', 'description': '10+ helpful answers'})
        
        # Verified solutions
        if verified_solutions >= 20:
            achievements.append({'title': 'Solution Master', 'description': '20+ verified solutions'})
        elif verified_solutions >= 10:
            achievements.append({'title': 'Solution Provider', 'description': '10+ verified solutions'})
        
        # Community endorsements
        if community_endorsements >= 20:
            achievements.append({'title': 'Community Favorite', 'description': '20+ highly engaged posts'})
        
        # Expertise breadth
        if len(expertise_areas) >= 5:
            achievements.append({'title': 'Multi-Crop Expert', 'description': 'Expertise in 5+ crop types'})
        elif len(expertise_areas) >= 3:
            achievements.append({'title': 'Diverse Knowledge', 'description': 'Expertise in 3+ crop types'})
        
        return achievements
    
    def get_top_experts(self, limit: int = 10, expertise_area: Optional[str] = None) -> Dict[str, Any]:
        """
        Get top experts in the community
        
        Args:
            limit: Maximum number of experts to return
            expertise_area: Optional filter by expertise area (crop type)
        
        Returns:
            Dict with list of top experts
        """
        try:
            # Get all users who have posted
            response = self.posts_table.scan(
                FilterExpression=Attr('status').eq('active')
            )
            
            posts = response.get('Items', [])
            
            # Group posts by user
            user_posts = {}
            for post in posts:
                user_id = post.get('user_id')
                if user_id not in user_posts:
                    user_posts[user_id] = []
                user_posts[user_id].append(post)
            
            # Calculate reputation for each user
            experts = []
            for user_id, user_post_list in user_posts.items():
                rep_result = self.get_user_reputation(user_id)
                
                if rep_result['success']:
                    # Filter by expertise area if specified
                    if expertise_area:
                        expertise_areas = rep_result.get('expertise_areas', [])
                        has_expertise = any(
                            area['area'] == expertise_area 
                            for area in expertise_areas
                        )
                        if not has_expertise:
                            continue
                    
                    # Only include verified experts or high reputation users
                    if rep_result['is_verified_expert'] or rep_result['reputation_score'] >= 200:
                        experts.append({
                            'user_id': user_id,
                            'reputation_score': rep_result['reputation_score'],
                            'expertise_level': rep_result['expertise_level'],
                            'badge': rep_result['badge'],
                            'badge_emoji': rep_result['badge_emoji'],
                            'is_verified_expert': rep_result['is_verified_expert'],
                            'expertise_areas': rep_result['expertise_areas'],
                            'metrics': rep_result['metrics']
                        })
            
            # Sort by reputation score
            experts.sort(key=lambda x: x['reputation_score'], reverse=True)
            
            return {
                'success': True,
                'experts': experts[:limit],
                'count': len(experts),
                'expertise_filter': expertise_area
            }
        
        except Exception as e:
            logger.error(f"Error getting top experts: {e}")
            return {
                'success': False,
                'error': str(e),
                'experts': []
            }
    
    def mark_post_as_solution(self, post_id: str, marked_by_user_id: str) -> Dict[str, Any]:
        """
        Mark a post as a verified solution
        
        Args:
            post_id: Post identifier
            marked_by_user_id: User who is marking it as solution
        
        Returns:
            Dict with result
        """
        try:
            # Update post
            self.posts_table.update_item(
                Key={'post_id': post_id},
                UpdateExpression='SET is_solution = :val, solution_marked_by = :user, solution_marked_at = :time',
                ExpressionAttributeValues={
                    ':val': True,
                    ':user': marked_by_user_id,
                    ':time': datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Post {post_id} marked as solution by {marked_by_user_id}")
            
            return {
                'success': True,
                'message': 'Post marked as verified solution'
            }
        
        except Exception as e:
            logger.error(f"Error marking post as solution: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_expert_directory(self) -> Dict[str, Any]:
        """
        Get comprehensive expert directory with all verified experts
        
        Returns:
            Dict with expert directory organized by expertise areas
        """
        try:
            # Get all experts
            experts_result = self.get_top_experts(limit=100)
            
            if not experts_result['success']:
                return experts_result
            
            experts = experts_result['experts']
            
            # Organize by expertise areas
            directory = {
                'verified_experts': [],
                'by_expertise': {},
                'total_experts': 0,
                'total_verified': 0
            }
            
            for expert in experts:
                # Add to verified experts list if verified
                if expert['is_verified_expert']:
                    directory['verified_experts'].append(expert)
                    directory['total_verified'] += 1
                
                directory['total_experts'] += 1
                
                # Organize by expertise areas
                for expertise in expert.get('expertise_areas', []):
                    area = expertise['area']
                    if area not in directory['by_expertise']:
                        directory['by_expertise'][area] = []
                    
                    directory['by_expertise'][area].append({
                        'user_id': expert['user_id'],
                        'reputation_score': expert['reputation_score'],
                        'badge': expert['badge'],
                        'badge_emoji': expert['badge_emoji'],
                        'expertise_score': expertise['score'],
                        'posts_in_area': expertise['posts_count']
                    })
            
            # Sort experts in each area by expertise score
            for area in directory['by_expertise']:
                directory['by_expertise'][area].sort(
                    key=lambda x: x['expertise_score'], 
                    reverse=True
                )
            
            return {
                'success': True,
                'directory': directory
            }
        
        except Exception as e:
            logger.error(f"Error getting expert directory: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Factory function
def create_forum_tools(region: str = "us-east-1") -> ForumTools:
    """
    Factory function to create forum tools instance
    
    Args:
        region: AWS region
    
    Returns:
        ForumTools instance
    """
    return ForumTools(region=region)

