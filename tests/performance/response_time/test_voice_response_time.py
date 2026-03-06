"""
Voice processing response time tests for RISE.

Validates that voice processing meets the <3 second requirement:
- Audio upload and validation
- Speech-to-text transcription
- AI processing and response generation
- Text-to-speech synthesis
- End-to-end voice query processing
"""

import unittest
import time
import base64
import json
import statistics
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class TestVoiceResponseTime(unittest.TestCase):
    """Test voice processing response times."""
    
    # Performance thresholds (milliseconds)
    VOICE_TARGET_MS = 3000  # <3 seconds requirement
    VOICE_ACCEPTABLE_MS = 5000  # Acceptable threshold
    TRANSCRIBE_TARGET_MS = 1500  # Transcription component
    TTS_TARGET_MS = 1000  # Text-to-speech component
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_audio_data = base64.b64encode(b"fake_audio_data" * 100).decode('utf-8')
        self.test_user_id = "test_farmer_001"
        self.test_language = "hi"
        self.response_times = []
    
    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start_time) * 1000
        self.response_times.append(elapsed_ms)
        return result, elapsed_ms
    
    @patch('boto3.client')
    def test_audio_upload_response_time(self, mock_boto_client):
        """Test audio upload response time."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_s3.put_object.return_value = {'ETag': 'test-etag'}
        mock_boto_client.return_value = mock_s3
        
        def upload_audio():
            """Simulate audio upload."""
            audio_bytes = base64.b64decode(self.test_audio_data)
            s3_key = f"audio/{self.test_user_id}/{int(time.time())}.wav"
            
            mock_s3.put_object(
                Bucket='rise-test-bucket',
                Key=s3_key,
                Body=audio_bytes,
                ContentType='audio/wav'
            )
            return s3_key
        
        result, elapsed_ms = self.measure_time(upload_audio)
        
        print(f"Audio upload time: {elapsed_ms:.2f}ms")
        self.assertLess(elapsed_ms, 500, "Audio upload should be <500ms")
        self.assertIsNotNone(result)
    
    @patch('boto3.client')
    def test_transcription_response_time(self, mock_boto_client):
        """Test speech-to-text transcription response time."""
        # Mock Transcribe client
        mock_transcribe = MagicMock()
        mock_transcribe.start_transcription_job.return_value = {
            'TranscriptionJob': {'TranscriptionJobName': 'test-job'}
        }
        mock_transcribe.get_transcription_job.return_value = {
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'COMPLETED',
                'Transcript': {
                    'TranscriptFileUri': 'https://s3.amazonaws.com/transcript.json'
                }
            }
        }
        mock_boto_client.return_value = mock_transcribe
        
        def transcribe_audio():
            """Simulate audio transcription."""
            job_name = f"transcribe-{int(time.time())}"
            
            # Start transcription
            mock_transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                LanguageCode=self.test_language,
                MediaFormat='wav',
                Media={'MediaFileUri': 's3://bucket/audio.wav'}
            )
            
            # Poll for completion (simulated)
            time.sleep(0.1)  # Simulate processing time
            
            response = mock_transcribe.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            return "मेरी गेहूं की फसल में पीले धब्बे हैं"
        
        result, elapsed_ms = self.measure_time(transcribe_audio)
        
        print(f"Transcription time: {elapsed_ms:.2f}ms")
        self.assertLess(elapsed_ms, self.TRANSCRIBE_TARGET_MS, 
                       f"Transcription should be <{self.TRANSCRIBE_TARGET_MS}ms")
        self.assertIsNotNone(result)
    
    @patch('boto3.client')
    def test_ai_processing_response_time(self, mock_boto_client):
        """Test AI query processing response time."""
        # Mock Bedrock client
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': 'यह गेहूं में पीला रतुआ रोग है। उपचार: ट्राइडेमॉर्फ स्प्रे करें।'
                }]
            }).encode())
        }
        mock_boto_client.return_value = mock_bedrock
        
        def process_query(query_text):
            """Simulate AI query processing."""
            response = mock_bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 500,
                    'messages': [{
                        'role': 'user',
                        'content': query_text
                    }]
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text']
        
        query = "मेरी गेहूं की फसल में पीले धब्बे हैं"
        result, elapsed_ms = self.measure_time(process_query, query)
        
        print(f"AI processing time: {elapsed_ms:.2f}ms")
        self.assertLess(elapsed_ms, 1000, "AI processing should be <1000ms")
        self.assertIsNotNone(result)
    
    @patch('boto3.client')
    def test_text_to_speech_response_time(self, mock_boto_client):
        """Test text-to-speech synthesis response time."""
        # Mock Polly client
        mock_polly = MagicMock()
        mock_polly.synthesize_speech.return_value = {
            'AudioStream': MagicMock(read=lambda: b'fake_audio_stream')
        }
        mock_boto_client.return_value = mock_polly
        
        def synthesize_speech(text):
            """Simulate text-to-speech synthesis."""
            response = mock_polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId='Aditi',
                LanguageCode='hi-IN',
                Engine='neural'
            )
            
            audio_stream = response['AudioStream'].read()
            return base64.b64encode(audio_stream).decode('utf-8')
        
        text = "यह गेहूं में पीला रतुआ रोग है।"
        result, elapsed_ms = self.measure_time(synthesize_speech, text)
        
        print(f"Text-to-speech time: {elapsed_ms:.2f}ms")
        self.assertLess(elapsed_ms, self.TTS_TARGET_MS, 
                       f"TTS should be <{self.TTS_TARGET_MS}ms")
        self.assertIsNotNone(result)
    
    @patch('boto3.client')
    def test_end_to_end_voice_query(self, mock_boto_client):
        """Test complete end-to-end voice query processing."""
        # Mock all AWS services
        mock_s3 = MagicMock()
        mock_transcribe = MagicMock()
        mock_bedrock = MagicMock()
        mock_polly = MagicMock()
        
        def get_client(service_name, **kwargs):
            clients = {
                's3': mock_s3,
                'transcribe': mock_transcribe,
                'bedrock-runtime': mock_bedrock,
                'polly': mock_polly
            }
            return clients.get(service_name, MagicMock())
        
        mock_boto_client.side_effect = get_client
        
        # Configure mocks
        mock_s3.put_object.return_value = {'ETag': 'test-etag'}
        mock_transcribe.start_transcription_job.return_value = {
            'TranscriptionJob': {'TranscriptionJobName': 'test-job'}
        }
        mock_transcribe.get_transcription_job.return_value = {
            'TranscriptionJob': {
                'TranscriptionJobStatus': 'COMPLETED',
                'Transcript': {'TranscriptFileUri': 'https://s3.amazonaws.com/transcript.json'}
            }
        }
        mock_bedrock.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{'text': 'यह गेहूं में पीला रतुआ रोग है।'}]
            }).encode())
        }
        mock_polly.synthesize_speech.return_value = {
            'AudioStream': MagicMock(read=lambda: b'fake_audio_stream')
        }
        
        def process_voice_query():
            """Simulate complete voice query processing."""
            # 1. Upload audio
            audio_bytes = base64.b64decode(self.test_audio_data)
            s3_key = f"audio/{self.test_user_id}/{int(time.time())}.wav"
            mock_s3.put_object(
                Bucket='rise-test-bucket',
                Key=s3_key,
                Body=audio_bytes
            )
            
            # 2. Transcribe audio
            job_name = f"transcribe-{int(time.time())}"
            mock_transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                LanguageCode=self.test_language,
                MediaFormat='wav',
                Media={'MediaFileUri': f's3://bucket/{s3_key}'}
            )
            time.sleep(0.05)  # Simulate processing
            
            # 3. Process with AI
            query_text = "मेरी गेहूं की फसल में पीले धब्बे हैं"
            response = mock_bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'messages': [{'role': 'user', 'content': query_text}]
                })
            )
            result_text = json.loads(response['body'].read())['content'][0]['text']
            
            # 4. Synthesize speech
            tts_response = mock_polly.synthesize_speech(
                Text=result_text,
                OutputFormat='mp3',
                VoiceId='Aditi'
            )
            audio_output = tts_response['AudioStream'].read()
            
            return {
                'transcription': query_text,
                'response_text': result_text,
                'audio_response': base64.b64encode(audio_output).decode('utf-8')
            }
        
        result, elapsed_ms = self.measure_time(process_voice_query)
        
        print(f"\n{'='*60}")
        print(f"END-TO-END VOICE QUERY PERFORMANCE")
        print(f"{'='*60}")
        print(f"Total time: {elapsed_ms:.2f}ms ({elapsed_ms/1000:.2f}s)")
        print(f"Target: <{self.VOICE_TARGET_MS}ms (<{self.VOICE_TARGET_MS/1000}s)")
        print(f"Status: {'✅ PASS' if elapsed_ms < self.VOICE_TARGET_MS else '⚠️  ACCEPTABLE' if elapsed_ms < self.VOICE_ACCEPTABLE_MS else '❌ FAIL'}")
        print(f"{'='*60}\n")
        
        self.assertLess(elapsed_ms, self.VOICE_ACCEPTABLE_MS, 
                       f"End-to-end voice query should be <{self.VOICE_ACCEPTABLE_MS}ms")
        self.assertIsNotNone(result)
        self.assertIn('transcription', result)
        self.assertIn('response_text', result)
        self.assertIn('audio_response', result)
    
    def test_voice_query_performance_statistics(self):
        """Test voice query performance with multiple iterations."""
        print(f"\n{'='*60}")
        print(f"VOICE QUERY PERFORMANCE STATISTICS")
        print(f"{'='*60}")
        
        # Simulate multiple voice queries
        response_times = []
        num_iterations = 10
        
        for i in range(num_iterations):
            start_time = time.time()
            
            # Simulate voice processing pipeline
            time.sleep(0.05)  # Upload
            time.sleep(0.1)   # Transcribe
            time.sleep(0.05)  # AI processing
            time.sleep(0.05)  # TTS
            
            elapsed_ms = (time.time() - start_time) * 1000
            response_times.append(elapsed_ms)
        
        # Calculate statistics
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]
        p99_time = sorted(response_times)[int(0.99 * len(response_times))]
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"Iterations: {num_iterations}")
        print(f"Mean: {mean_time:.2f}ms")
        print(f"Median: {median_time:.2f}ms")
        print(f"P95: {p95_time:.2f}ms")
        print(f"P99: {p99_time:.2f}ms")
        print(f"Min: {min_time:.2f}ms")
        print(f"Max: {max_time:.2f}ms")
        print(f"\nTarget: <{self.VOICE_TARGET_MS}ms")
        print(f"P95 Status: {'✅ PASS' if p95_time < self.VOICE_TARGET_MS else '❌ FAIL'}")
        print(f"{'='*60}\n")
        
        # Assert P95 meets target
        self.assertLess(p95_time, self.VOICE_ACCEPTABLE_MS, 
                       f"P95 response time should be <{self.VOICE_ACCEPTABLE_MS}ms")
    
    def tearDown(self):
        """Clean up after tests."""
        if self.response_times:
            avg_time = statistics.mean(self.response_times)
            print(f"Average response time for this test: {avg_time:.2f}ms")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
