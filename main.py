#!/usr/bin/env python3
"""
NEXEO PREMIUM - Ultimate Media Downloader with Dark/Light Mode
Advanced UI/UX with premium loading animations
Deployment ready for Vercel with Proxy Support
Run: python nexeo.py
"""

import requests
import json
import uuid
import time
import logging
import re
import os
from flask import Flask, render_template_string, request, jsonify, send_file
from datetime import datetime
from functools import wraps
import io
from urllib.parse import urlparse

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexeo-premium-2026')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration - Multiple endpoints for fallback
API_URLS = [
    "https://api.easydownloader.app/api-extract/",
    "https://easydownloader.app/api-extract/",
    "https://api.savetube.me/api/extract"
]

API_KEY = os.environ.get('EASY_DOWNLOADER_API_KEY', '177p96593i9x5ase4.eivdoidjvsioiui-hNn?_oreesae&_eimrfra&_apinln')

# Different user agents to avoid blocking
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
]

def get_random_headers():
    """Get random headers to avoid blocking"""
    return {
        'User-Agent': USER_AGENTS[int(time.time()) % len(USER_AGENTS)],
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'Origin': 'https://easydownloader.app',
        'Referer': 'https://easydownloader.app/',
        'Sec-Ch-Ua': '"Chromium";v="146", "Not-A.Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

def extract_all_media(video_url, pagination=False):
    """Extract all media types with multiple API fallback"""
    
    # Try multiple API endpoints
    for api_index, API_URL in enumerate(API_URLS):
        payload = {
            "video_url": video_url,
            "pagination": pagination,
            "key": API_KEY
        }
        
        # Retry logic for each API
        max_retries = 2
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                headers = get_random_headers()
                logger.info(f"Trying API {api_index + 1}/{len(API_URLS)} - Attempt {attempt + 1}: {API_URL}")
                
                response = requests.post(API_URL, json=payload, headers=headers, timeout=45)
                
                logger.info(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"API Response Keys: {list(data.keys())}")
                        
                        if data.get('status') == 'success':
                            # Process successful response
                            images = []
                            videos = []
                            audio = []
                            video_title = "Media"
                            thumbnail = None
                            duration = None
                            
                            if 'final_urls' in data and data['final_urls']:
                                video_data = data['final_urls'][0]
                                video_title = video_data.get('title', 'Media')
                                thumbnail = video_data.get('thumb')
                                
                                if 'duration' in video_data:
                                    duration = video_data.get('duration')
                                
                                if thumbnail:
                                    images.append({
                                        'type': 'thumbnail',
                                        'url': thumbnail,
                                        'quality': 'HD Thumbnail',
                                        'size': None,
                                        'ext': 'webp'
                                    })
                                
                                if 'links' in video_data:
                                    for link in video_data['links']:
                                        link_url = link.get('link_url')
                                        file_quality = link.get('file_quality', 'Unknown')
                                        file_type = link.get('file_type', 'mp4')
                                        file_group = link.get('file_quality_group', 'video')
                                        file_size = link.get('file_size')
                                        
                                        if link_url:
                                            media_item = {
                                                'quality': file_quality,
                                                'url': link_url,
                                                'size': file_size,
                                                'ext': file_type,
                                                'group': file_group
                                            }
                                            
                                            if file_group == 'video':
                                                videos.append(media_item)
                                            elif file_group == 'audio':
                                                audio.append(media_item)
                                            else:
                                                videos.append(media_item)
                            
                            # Remove duplicates
                            unique_videos = []
                            seen_urls = set()
                            for vid in videos:
                                if vid['url'] not in seen_urls:
                                    seen_urls.add(vid['url'])
                                    unique_videos.append(vid)
                            
                            # Sort videos by quality
                            def get_quality_number(q):
                                if '1080' in q or '1920x1080' in q:
                                    return 1080
                                elif '720' in q or '1280x720' in q:
                                    return 720
                                elif '480' in q or '854x480' in q:
                                    return 480
                                elif '360' in q or '640x360' in q:
                                    return 360
                                elif '240' in q or '426x240' in q:
                                    return 240
                                elif '144' in q or '256x144' in q:
                                    return 144
                                return 0
                            
                            unique_videos.sort(key=lambda x: get_quality_number(x['quality']), reverse=True)
                            audio.sort(key=lambda x: x['quality'])
                            
                            return {
                                'success': True,
                                'title': video_title,
                                'thumbnail': thumbnail,
                                'duration': duration,
                                'images': images,
                                'videos': unique_videos,
                                'audio': audio,
                                'total_videos': len(unique_videos),
                                'total_audio': len(audio),
                                'timestamp': datetime.now().isoformat(),
                                'api_used': API_URL
                            }
                        else:
                            error_msg = data.get('msg', 'API returned error status')
                            logger.warning(f"API error: {error_msg}")
                            if attempt == max_retries - 1:
                                continue
                            time.sleep(retry_delay)
                            continue
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}, Response: {response.text[:200]}")
                        if attempt == max_retries - 1:
                            continue
                        time.sleep(retry_delay)
                        continue
                else:
                    logger.warning(f"HTTP {response.status_code} from {API_URL}")
                    if attempt == max_retries - 1:
                        continue
                    time.sleep(retry_delay)
                    continue
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    continue
                time.sleep(retry_delay)
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    continue
                time.sleep(retry_delay)
                
            except Exception as e:
                logger.error(f"Extraction error: {str(e)}")
                if attempt == max_retries - 1:
                    continue
                time.sleep(retry_delay)
    
    # If all APIs fail
    return {
        'success': False,
        'error': 'Unable to extract media. Please check the URL or try again later.',
        'details': 'All API endpoints failed'
    }

# Advanced HTML Template with Enhanced Features
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <meta name="description" content="NEXEO PREMIUM - Ultimate Media Downloader. Download videos, audio, and images from various platforms with premium quality.">
    <title>NEXEO PREMIUM | Ultimate Media Downloader</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        :root {
            --bg-primary: linear-gradient(135deg, #f5f7fa 0%, #eef2f7 100%);
            --bg-secondary: rgba(255, 255, 255, 0.85);
            --card-bg: rgba(255, 255, 255, 0.75);
            --text-primary: #1a1a2e;
            --text-secondary: #4a5568;
            --border-color: rgba(0, 0, 0, 0.1);
            --accent-primary: #6366f1;
            --accent-secondary: #a855f7;
            --accent-tertiary: #ec489a;
            --shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
            --input-bg: rgba(255, 255, 255, 0.9);
            --section-bg: rgba(255, 255, 255, 0.6);
            --success: #10b981;
            --error: #ef4444;
            --warning: #f59e0b;
        }

        body.dark {
            --bg-primary: radial-gradient(circle at 20% 50%, #0a0f1e, #03050b);
            --bg-secondary: rgba(15, 23, 42, 0.85);
            --card-bg: rgba(15, 23, 42, 0.75);
            --text-primary: #ffffff;
            --text-secondary: #94a3b8;
            --border-color: rgba(99, 102, 241, 0.2);
            --accent-primary: #6366f1;
            --accent-secondary: #a855f7;
            --accent-tertiary: #ec489a;
            --shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            --input-bg: rgba(0, 0, 0, 0.5);
            --section-bg: rgba(0, 0, 0, 0.3);
            --success: #10b981;
            --error: #ef4444;
            --warning: #f59e0b;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            transition: background-color 0.3s ease, color 0.2s ease, border-color 0.3s ease, transform 0.2s ease;
        }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: var(--bg-primary);
            min-height: 100vh;
            color: var(--text-primary);
            overflow-x: hidden;
            position: relative;
        }

        .animated-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            overflow: hidden;
        }

        .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.3;
            animation: float 20s infinite ease-in-out;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -30px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
        }

        body.dark .orb {
            opacity: 0.2;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
            position: relative;
            z-index: 2;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            flex-wrap: wrap;
            gap: 20px;
            animation: slideDown 0.6s ease;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .logo-section {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            padding: 12px 28px;
            border-radius: 60px;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow);
        }

        .logo i {
            font-size: 40px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary), var(--accent-tertiary));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .logo h1 {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary), var(--accent-tertiary));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .theme-toggle {
            position: relative;
            width: 70px;
            height: 35px;
            background: var(--card-bg);
            border-radius: 50px;
            cursor: pointer;
            border: 1px solid var(--border-color);
            backdrop-filter: blur(10px);
            transition: all 0.3s;
        }

        .theme-toggle-slider {
            position: absolute;
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 50%;
            top: 3px;
            left: 4px;
            transition: transform 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }

        .theme-toggle-slider i {
            font-size: 14px;
            color: white;
        }

        body.dark .theme-toggle-slider {
            transform: translateX(34px);
        }

        .premium-loader {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            backdrop-filter: blur(30px);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            flex-direction: column;
            gap: 35px;
        }

        .loader-container {
            position: relative;
            width: 150px;
            height: 150px;
        }

        .loader-ring-premium {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 3px solid transparent;
            border-top-color: #6366f1;
            animation: spin 1.2s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
        }

        .loader-ring-premium:nth-child(2) {
            width: 80%;
            height: 80%;
            top: 10%;
            left: 10%;
            border-top-color: #a855f7;
            animation: spin 0.9s reverse infinite;
        }

        .loader-ring-premium:nth-child(3) {
            width: 60%;
            height: 60%;
            top: 20%;
            left: 20%;
            border-top-color: #ec489a;
            animation: spin 0.7s linear infinite;
        }

        .loader-ring-premium:nth-child(4) {
            width: 40%;
            height: 40%;
            top: 30%;
            left: 30%;
            border-top-color: #f59e0b;
            animation: spin 0.5s reverse infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .loader-text-premium {
            font-size: 1.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #6366f1, #a855f7, #ec489a);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            letter-spacing: 2px;
        }

        .loader-progress {
            width: 300px;
            height: 4px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }

        .loader-progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #a855f7, #ec489a);
            width: 0%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border-radius: 32px;
            border: 1px solid var(--border-color);
            padding: 40px;
            box-shadow: var(--shadow);
            transition: all 0.3s;
        }

        .input-group {
            margin-bottom: 25px;
        }

        .url-input-wrapper {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .url-input {
            flex: 1;
            background: var(--input-bg);
            border: 2px solid var(--border-color);
            border-radius: 24px;
            padding: 16px 24px;
            color: var(--text-primary);
            font-size: 1rem;
            transition: all 0.3s;
        }

        .url-input:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            padding: 14px 32px;
            border-radius: 24px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            border: none;
            font-size: 1rem;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            box-shadow: 0 5px 20px rgba(99, 102, 241, 0.4);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.6);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .batch-download {
            margin-top: 15px;
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }

        .btn-secondary {
            background: rgba(99, 102, 241, 0.2);
            color: var(--accent-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: rgba(99, 102, 241, 0.3);
            transform: translateY(-2px);
        }

        .results {
            margin-top: 40px;
            display: none;
            animation: fadeInUp 0.6s ease;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .image-section {
            margin-bottom: 40px;
        }

        .media-preview {
            background: var(--section-bg);
            border-radius: 28px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            max-width: 500px;
            margin: 0 auto;
        }

        .media-preview img {
            width: 100%;
            height: auto;
            display: block;
        }

        .media-title {
            padding: 20px;
            text-align: center;
            border-top: 1px solid var(--border-color);
        }

        .media-title h2 {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--text-primary);
        }

        .media-title p {
            color: var(--text-secondary);
            font-size: 0.85rem;
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin: 30px 0 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--border-color);
        }

        .section-header i {
            font-size: 28px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .section-header h3 {
            font-size: 1.5rem;
            font-weight: 700;
        }

        .section-header span {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 0.8rem;
            color: white;
        }

        .media-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }

        .media-card {
            background: var(--section-bg);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
            border: 1px solid var(--border-color);
        }

        .media-card:hover {
            border-color: var(--accent-primary);
            transform: translateY(-3px);
        }

        .media-info {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .media-quality {
            font-weight: 800;
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .media-meta {
            font-size: 0.7rem;
            color: var(--text-secondary);
            display: flex;
            gap: 12px;
        }

        .download-btn {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            border: none;
            padding: 10px 18px;
            border-radius: 14px;
            color: white;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
        }

        .download-btn:hover {
            transform: scale(1.05);
        }

        .checkbox-select {
            margin-right: 15px;
        }

        .checkbox-select input {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }

        .error-box {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid var(--error);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            color: var(--error);
        }

        .success-box {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid var(--success);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            color: var(--success);
        }

        .warning-box {
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid var(--warning);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            color: var(--warning);
        }

        .footer {
            text-align: center;
            margin-top: 50px;
            padding: 25px;
            color: var(--text-secondary);
            border-top: 1px solid var(--border-color);
        }

        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            z-index: 1001;
            animation: slideInRight 0.3s ease;
            box-shadow: var(--shadow);
        }

        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @media (max-width: 768px) {
            .container { padding: 15px; }
            .card { padding: 25px; }
            .logo h1 { font-size: 1.5rem; }
            .logo i { font-size: 28px; }
            .media-grid { grid-template-columns: 1fr; }
            .section-header h3 { font-size: 1.2rem; }
            .toast { bottom: 20px; right: 20px; left: 20px; }
        }
    </style>
</head>
<body>

<div class="animated-bg">
    <div class="orb" style="width: 400px; height: 400px; background: #6366f1; top: -100px; left: -100px; animation-delay: 0s;"></div>
    <div class="orb" style="width: 500px; height: 500px; background: #a855f7; bottom: -150px; right: -100px; animation-delay: 2s;"></div>
    <div class="orb" style="width: 300px; height: 300px; background: #ec489a; top: 50%; left: 50%; animation-delay: 4s;"></div>
</div>

<div class="premium-loader" id="premiumLoader">
    <div class="loader-container">
        <div class="loader-ring-premium"></div>
        <div class="loader-ring-premium"></div>
        <div class="loader-ring-premium"></div>
        <div class="loader-ring-premium"></div>
    </div>
    <div class="loader-text-premium" id="loaderText">PROCESSING</div>
    <div class="loader-progress">
        <div class="loader-progress-bar" id="loaderProgress"></div>
    </div>
    <div style="color: #94a3b8; font-size: 0.85rem;" id="loaderStatus">Initializing secure connection...</div>
</div>

<div class="container">
    <div class="header">
        <div class="logo-section">
            <div class="logo">
                <i class="fas fa-crown"></i>
                <h1>NEXEO PREMIUM</h1>
            </div>
        </div>
        <div class="theme-toggle" id="themeToggle">
            <div class="theme-toggle-slider">
                <i class="fas fa-sun" id="themeIcon"></i>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="input-group">
            <div class="url-input-wrapper">
                <input type="text" class="url-input" id="videoUrl" 
                       placeholder="https://hi.xhamster44.desi/videos/..." 
                       value="https://hi.xhamster44.desi/videos/wild-jav-shino-izumis-xhWN4nw?utm_source=ext_shared&utm_medium=referral&utm_campaign=link">
                <button class="btn btn-primary" id="extractBtn">
                    <i class="fas fa-magic"></i> Extract Media
                </button>
            </div>
            <div class="batch-download">
                <button class="btn btn-secondary" id="batchDownloadBtn" style="display: none;">
                    <i class="fas fa-download"></i> Download Selected (0)
                </button>
            </div>
        </div>

        <div id="resultsArea"></div>
    </div>

    <div class="footer">
        <i class="fas fa-shield-alt"></i> Premium Security • Multi-API Fallback • Instant Downloads
    </div>
</div>

<script>
    let currentMediaData = null;
    let selectedItems = new Set();
    
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    
    function setTheme(theme) {
        if (theme === 'dark') {
            document.body.classList.add('dark');
            themeIcon.className = 'fas fa-moon';
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark');
            themeIcon.className = 'fas fa-sun';
            localStorage.setItem('theme', 'light');
        }
    }
    
    function toggleTheme() {
        if (document.body.classList.contains('dark')) {
            setTheme('light');
        } else {
            setTheme('dark');
        }
    }
    
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        setTheme('dark');
    } else {
        setTheme('light');
    }
    
    themeToggle.addEventListener('click', toggleTheme);
    
    const videoUrlInput = document.getElementById('videoUrl');
    const extractBtn = document.getElementById('extractBtn');
    const batchDownloadBtn = document.getElementById('batchDownloadBtn');
    const premiumLoader = document.getElementById('premiumLoader');
    const loaderText = document.getElementById('loaderText');
    const loaderProgress = document.getElementById('loaderProgress');
    const loaderStatus = document.getElementById('loaderStatus');
    const resultsArea = document.getElementById('resultsArea');
    
    function showToast(message, type = 'error') {
        const toast = document.createElement('div');
        toast.className = 'toast';
        const icon = type === 'error' ? 'fa-exclamation-circle' : (type === 'success' ? 'fa-check-circle' : 'fa-info-circle');
        toast.innerHTML = `<i class="fas ${icon}" style="color: var(--${type})"></i><span>${message}</span>`;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    function updateLoaderProgress(percent, text, status) {
        loaderProgress.style.width = percent + '%';
        if (text) loaderText.innerText = text;
        if (status) loaderStatus.innerText = status;
    }
    
    function showLoading() {
        updateLoaderProgress(0, 'INITIALIZING', 'Starting extraction engine...');
        premiumLoader.style.display = 'flex';
        
        let progress = 0;
        const interval = setInterval(() => {
            if (progress < 90) {
                progress += Math.random() * 10;
                if (progress > 90) progress = 90;
                loaderProgress.style.width = progress + '%';
            }
        }, 300);
        
        window.loaderInterval = interval;
    }
    
    function hideLoading() {
        if (window.loaderInterval) {
            clearInterval(window.loaderInterval);
        }
        loaderProgress.style.width = '100%';
        setTimeout(() => {
            premiumLoader.style.display = 'none';
            loaderProgress.style.width = '0%';
        }, 300);
    }
    
    function formatBytes(bytes) {
        if (!bytes) return 'Unknown size';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
    }
    
    function downloadMedia(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || 'media';
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        showToast('Download started!', 'success');
    }
    
    function toggleSelection(itemId, url, filename) {
        if (selectedItems.has(itemId)) {
            selectedItems.delete(itemId);
        } else {
            selectedItems.add({id: itemId, url: url, filename: filename});
        }
        updateBatchButton();
    }
    
    function updateBatchButton() {
        const count = selectedItems.size;
        if (count > 0) {
            batchDownloadBtn.style.display = 'inline-flex';
            batchDownloadBtn.innerHTML = `<i class="fas fa-download"></i> Download Selected (${count})`;
        } else {
            batchDownloadBtn.style.display = 'none';
        }
    }
    
    function downloadBatch() {
        if (selectedItems.size === 0) return;
        
        showToast(`Downloading ${selectedItems.size} items...`, 'success');
        selectedItems.forEach(item => {
            setTimeout(() => {
                downloadMedia(item.url, item.filename);
            }, 500);
        });
        
        selectedItems.clear();
        updateBatchButton();
        renderResults(currentMediaData); // Re-render to clear checkboxes
    }
    
    async function extractMedia() {
        const url = videoUrlInput.value.trim();
        if (!url) {
            resultsArea.innerHTML = `
                <div class="error-box">
                    <i class="fas fa-exclamation-triangle" style="font-size: 24px;"></i>
                    <span>Please enter a valid video URL</span>
                </div>`;
            showToast('Please enter a valid URL', 'error');
            return;
        }
        
        showLoading();
        updateLoaderProgress(10, 'ANALYZING', 'Validating URL...');
        resultsArea.innerHTML = '';
        
        try {
            updateLoaderProgress(30, 'FETCHING', 'Connecting to media servers...');
            
            const response = await fetch('/api/extract-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_url: url })
            });
            
            updateLoaderProgress(60, 'PARSING', 'Processing media data...');
            const data = await response.json();
            
            updateLoaderProgress(80, 'RENDERING', 'Building media gallery...');
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || data.details || 'Failed to extract media');
            }
            
            currentMediaData = data;
            selectedItems.clear();
            
            updateLoaderProgress(100, 'COMPLETE', 'Ready!');
            setTimeout(() => {
                renderResults(data);
                hideLoading();
                showToast('Media extracted successfully!', 'success');
            }, 500);
            
        } catch (error) {
            updateLoaderProgress(0, 'ERROR', error.message);
            setTimeout(() => {
                resultsArea.innerHTML = `
                    <div class="error-box">
                        <i class="fas fa-skull" style="font-size: 24px;"></i>
                        <span>${escapeHtml(error.message)}</span>
                    </div>`;
                hideLoading();
                showToast(error.message, 'error');
            }, 1000);
        }
    }
    
    function renderResults(data) {
        const title = data.title || 'Media';
        const images = data.images || [];
        const videos = data.videos || [];
        const audio = data.audio || [];
        
        let html = `<div class="results" style="display: block;">`;
        
        html += `<div class="image-section">`;
        if (images.length > 0 && images[0].url) {
            html += `
                <div class="media-preview">
                    <img src="${escapeHtml(images[0].url)}" alt="Thumbnail" onerror="this.src='https://via.placeholder.com/800x450?text=No+Preview'">
                    <div class="media-title">
                        <h2>${escapeHtml(title)}</h2>
                        <p><i class="fas fa-calendar"></i> Premium Quality • HD Available</p>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="media-preview">
                    <div style="background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); height: 200px; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-play-circle" style="font-size: 60px; color: white; opacity: 0.7;"></i>
                    </div>
                    <div class="media-title">
                        <h2>${escapeHtml(title)}</h2>
                        <p><i class="fas fa-video"></i> Video Content</p>
                    </div>
                </div>
            `;
        }
        html += `</div>`;
        
        if (videos.length > 0) {
            html += `
                <div class="section-header">
                    <i class="fas fa-video"></i>
                    <h3>Video Qualities</h3>
                    <span>${videos.length} options</span>
                </div>
                <div class="media-grid">
            `;
            
            videos.forEach((video, index) => {
                const quality = video.quality || 'Standard';
                const ext = video.ext || 'mp4';
                const size = video.size;
                const sizeStr = formatBytes(size);
                const itemId = `video_${index}`;
                
                let qualityIcon = 'fa-video';
                if (quality.includes('1080')) qualityIcon = 'fa-4k';
                else if (quality.includes('720')) qualityIcon = 'fa-hd';
                else if (quality.includes('480')) qualityIcon = 'fa-film';
                
                html += `
                    <div class="media-card">
                        <div class="checkbox-select">
                            <input type="checkbox" onchange="toggleSelection('${itemId}', '${escapeHtml(video.url)}', '${escapeHtml(title)}_${quality}.${ext}')">
                        </div>
                        <div class="media-info">
                            <div class="media-quality">
                                <i class="fas ${qualityIcon}"></i>
                                <span>${escapeHtml(quality)}</span>
                            </div>
                            <div class="media-meta">
                                <span><i class="fas fa-file"></i> ${ext.toUpperCase()}</span>
                                <span><i class="fas fa-database"></i> ${sizeStr}</span>
                            </div>
                        </div>
                        <button class="download-btn" onclick="downloadMedia('${escapeHtml(video.url)}', '${escapeHtml(title)}_${quality}.${ext}')">
                            <i class="fas fa-download"></i> Get
                        </button>
                    </div>
                `;
            });
            
            html += `</div>`;
        }
        
        if (audio.length > 0) {
            html += `
                <div class="section-header">
                    <i class="fas fa-music"></i>
                    <h3>Audio Tracks</h3>
                    <span>${audio.length} tracks</span>
                </div>
                <div class="media-grid">
            `;
            
            audio.forEach((track, index) => {
                const quality = track.quality || 'Audio';
                const ext = track.ext || 'mp3';
                const size = track.size;
                const sizeStr = formatBytes(size);
                const itemId = `audio_${index}`;
                
                html += `
                    <div class="media-card">
                        <div class="checkbox-select">
                            <input type="checkbox" onchange="toggleSelection('${itemId}', '${escapeHtml(track.url)}', '${escapeHtml(title)}_audio.${ext}')">
                        </div>
                        <div class="media-info">
                            <div class="media-quality">
                                <i class="fas fa-headphones"></i>
                                <span>${escapeHtml(quality)}</span>
                            </div>
                            <div class="media-meta">
                                <span><i class="fas fa-file-audio"></i> ${ext.toUpperCase()}</span>
                                <span><i class="fas fa-database"></i> ${sizeStr}</span>
                            </div>
                        </div>
                        <button class="download-btn" onclick="downloadMedia('${escapeHtml(track.url)}', '${escapeHtml(title)}_audio.${ext}')">
                            <i class="fas fa-download"></i> Get
                        </button>
                    </div>
                `;
            });
            
            html += `</div>`;
        }
        
        if (videos.length === 0 && audio.length === 0) {
            html += `
                <div class="warning-box">
                    <i class="fas fa-info-circle" style="font-size: 24px;"></i>
                    <span>No downloadable media found. Try another video source.</span>
                </div>
            `;
        }
        
        html += `</div>`;
        resultsArea.innerHTML = html;
        updateBatchButton();
    }
    
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    extractBtn.addEventListener('click', extractMedia);
    batchDownloadBtn.addEventListener('click', downloadBatch);
    videoUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') extractMedia();
    });
    
    setTimeout(() => extractMedia(), 500);
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/extract-all', methods=['POST'])
def api_extract_all():
    try:
        data = request.get_json()
        if not data or 'video_url' not in data:
            return jsonify({'success': False, 'error': 'Missing video_url'}), 400
        
        video_url = data['video_url'].strip()
        pagination = data.get('pagination', False)
        
        result = extract_all_media(video_url, pagination)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Vercel"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0'
    })

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║           NEXEO PREMIUM - ULTIMATE MEDIA DOWNLOADER              ║
    ║                         Version 3.0.0                            ║
    ║                                                                  ║
    ║     🖼️  Images at Top | 📝 Title Below | 🎬 Videos | 🎵 Audio   ║
    ║                                                                  ║
    ║     🌓 Dark/Light Mode Toggle (Click the sun/moon icon)          ║
    ║     🚀 Premium 4-Ring Loading Animation                         ║
    ║     💎 Ultra Advanced UI/UX Design                              ║
    ║     🔄 Multi-API Fallback (3 endpoints)                         ║
    ║     📦 Batch Download with Checkbox Selection                   ║
    ║     🔔 Toast Notifications for user feedback                    ║
    ║                                                                  ║
    ║     🔗 Server: http://127.0.0.1:5000                            ║
    ║     💚 Health Check: http://127.0.0.1:5000/health               ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
