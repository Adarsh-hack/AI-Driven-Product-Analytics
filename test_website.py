"""
Test Website for Analytics Simulation

This script creates a simple Flask application that runs on port 5001
to simulate a website with analytics tracking. It allows you to test
your analytics implementation by generating events and seeing them
in real-time.

Usage:
  1. Save this file as test_website.py in a 'test' folder
  2. Run with: python test_website.py
  3. Access the test website at: http://localhost:5001/test/<project_id>

"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, render_template_string
import requests
import json
import uuid
import datetime
import random
import time
import os
from threading import Thread

# Create Flask app
app = Flask(__name__)

# Configuration
PORT = 5001
MAIN_APP_URL = "http://localhost:5000"
API_ENDPOINT = f"{MAIN_APP_URL}/api/events"
API_TEST_ENDPOINT = f"{MAIN_APP_URL}/api/events/test"

# In-memory storage for events
events = []

# Create test_templates directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)

# Create the HTML templates
index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analytics Test Page</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        primary: {
                            DEFAULT: '#6366f1',
                            dark: '#4f46e5',
                            light: '#818cf8'
                        },
                        dark: {
                            DEFAULT: '#1e1e2d',
                            lighter: '#2d2d3a',
                            lightest: '#34343f'
                        }
                    }
                }
            }
        }
    </script>
    <style>
        /* Animation for event indicators */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .pulse-animation {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        /* Animation for event transmission */
        @keyframes sendEvent {
            0% { transform: scale(1); }
            50% { transform: scale(1.5); opacity: 0.7; }
            100% { transform: scale(1); }
        }
        .send-event {
            animation: sendEvent 0.5s ease-in-out;
        }
        
        /* Loading spinner */
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .spinner {
            animation: spin 1s linear infinite;
        }
        
        /* JSON syntax highlighting */
        .json-key { color: #f59e0b; }
        .json-string { color: #10b981; }
        .json-number { color: #3b82f6; }
        .json-boolean { color: #8b5cf6; }
        .json-null { color: #ef4444; }
    </style>
    
    {% if tracking_id %}
        <!-- Analytics tracking code -->
        <script>
            (function(window, document) {
                // Create analytics object if it doesn't exist
                window.ProductAnalytics = window.ProductAnalytics || {};
                
                // Configuration
                var config = {
                    apiEndpoint: '{{ api_endpoint }}',
                    projectId: '{{ tracking_id }}',
                    userId: null,
                    anonymousId: null
                };
                
                // Initialize the tracker
                window.ProductAnalytics.init = function(options) {
                    if (options) {
                        config.userId = options.userId || null;
                        config.apiEndpoint = options.apiEndpoint || config.apiEndpoint;
                    }
                    
                    // Generate anonymous ID if not set
                    if (!config.anonymousId) {
                        config.anonymousId = generateId();
                    }
                    
                    console.log('Product Analytics initialized for project:', config.projectId);
                    
                    // Dispatch event to notify the UI
                    document.dispatchEvent(new CustomEvent('analytics-initialized', { 
                        detail: { projectId: config.projectId } 
                    }));
                };
                
                // Track an event
                window.ProductAnalytics.track = function(eventName, properties) {
                    if (!config.projectId) {
                        console.error('Product Analytics not initialized');
                        return;
                    }
                    
                    var eventData = {
                        project_id: config.projectId,
                        event_name: eventName,
                        properties: properties || {},
                        user_id: config.userId,
                        anonymous_id: config.anonymousId,
                        timestamp: new Date().toISOString()
                    };
                    
                    // Dispatch event to notify the UI before sending
                    document.dispatchEvent(new CustomEvent('analytics-event-tracked', { 
                        detail: { eventData: eventData } 
                    }));
                    
                    // Send the event data to the server
                    sendEvent(eventData);
                };
                
                // Set user ID
                window.ProductAnalytics.setUserId = function(userId) {
                    config.userId = userId;
                    
                    // Dispatch event to notify the UI
                    document.dispatchEvent(new CustomEvent('analytics-user-set', { 
                        detail: { userId: userId } 
                    }));
                    
                    console.log('User ID set:', userId);
                };
                
                // Helper function to generate ID
                function generateId() {
                    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                        return v.toString(16);
                    });
                }
                
                // Helper function to send event data
                function sendEvent(eventData) {
                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', config.apiEndpoint, true);
                    xhr.setRequestHeader('Content-Type', 'application/json');
                    xhr.onreadystatechange = function() {
                        if (xhr.readyState === 4) {
                            var success = xhr.status === 200;
                            // Dispatch event to notify the UI
                            document.dispatchEvent(new CustomEvent('analytics-event-sent', { 
                                detail: { 
                                    success: success, 
                                    status: xhr.status,
                                    eventData: eventData
                                } 
                            }));
                            
                            if (success) {
                                console.log('Event tracked:', eventData.event_name);
                            } else {
                                console.error('Failed to track event:', xhr.statusText);
                            }
                        }
                    };
                    xhr.send(JSON.stringify(eventData));
                }
                
                // Initialize automatically
                window.ProductAnalytics.init();
                
                // Simplified alias
                window.pa = window.ProductAnalytics;
            })(window, document);
        </script>
    {% endif %}
</head>
<body class="bg-gray-900 text-gray-200 min-h-screen">
    <div class="min-h-screen flex flex-col">
        <!-- Header -->
        <header class="bg-dark-lighter border-b border-gray-700 py-4 px-6">
            <div class="max-w-6xl mx-auto flex justify-between items-center">
                <div class="flex items-center">
                    <svg class="h-8 w-8 text-primary-light mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                    <div>
                        <h1 class="text-xl font-bold text-white">Analytics Test Page</h1>
                        <p class="text-sm text-gray-400">Track events and test your implementation</p>
                    </div>
                </div>
                <div class="flex items-center space-x-3">
                    <div class="text-right">
                        <div class="flex items-center">
                            <div id="connection-status" class="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                            <span id="connection-text" class="text-sm text-gray-400">Checking connection...</span>
                        </div>
                        <div class="text-xs text-gray-500 mt-1" id="project-id-display">
                            Project ID: {{ tracking_id if tracking_id else "Not set" }}
                        </div>
                    </div>
                    <a href="{{ main_app_url }}/projects/{{ project_id }}" target="_blank" class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-md text-sm transition-colors">
                        <svg class="h-4 w-4 inline-block mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                        </svg>
                        Back to Project
                    </a>
                </div>
            </div>
        </header>
        
        <!-- Main Content -->
        <main class="flex-grow p-6">
            <div class="max-w-6xl mx-auto">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Event Simulation Panel -->
                    <div class="lg:col-span-2 space-y-6">
                        <!-- Demo Website Section -->
                        <div class="bg-dark-lighter rounded-lg border border-gray-700 overflow-hidden">
                            <div class="px-4 py-3 border-b border-gray-700 flex justify-between items-center">
                                <h2 class="font-medium text-white">Demo Website</h2>
                                <span class="px-2 py-1 bg-blue-900 bg-opacity-30 text-blue-300 rounded-full text-xs">Test Environment</span>
                            </div>
                            <div class="p-6">
                                <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                                    <h1 class="text-xl font-bold text-white mb-4">Welcome to Our Product</h1>
                                    <p class="text-gray-300 mb-6">This is a demo website to test analytics tracking. Try interacting with elements below to generate events.</p>
                                    
                                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                        <a href="javascript:void(0)" onclick="navigate('/home')" class="bg-gray-700 hover:bg-gray-600 p-4 rounded-lg text-center transition-colors">
                                            <svg class="h-8 w-8 mx-auto mb-2 text-primary-light" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7m-7-7v14"></path>
                                            </svg>
                                            Home Page
                                        </a>
                                        <a href="javascript:void(0)" onclick="navigate('/products')" class="bg-gray-700 hover:bg-gray-600 p-4 rounded-lg text-center transition-colors">
                                            <svg class="h-8 w-8 mx-auto mb-2 text-primary-light" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"></path>
                                            </svg>
                                            Products
                                        </a>
                                        <a href="javascript:void(0)" onclick="navigate('/about')" class="bg-gray-700 hover:bg-gray-600 p-4 rounded-lg text-center transition-colors">
                                            <svg class="h-8 w-8 mx-auto mb-2 text-primary-light" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                            </svg>
                                            About Us
                                        </a>
                                        <a href="javascript:void(0)" onclick="navigate('/contact')" class="bg-gray-700 hover:bg-gray-600 p-4 rounded-lg text-center transition-colors">
                                            <svg class="h-8 w-8 mx-auto mb-2 text-primary-light" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                                            </svg>
                                            Contact
                                        </a>
                                    </div>
                                    
                                    <div class="flex justify-between items-end mb-4">
                                        <h2 class="text-lg font-medium text-white">Featured Product</h2>
                                        <span class="text-sm text-gray-400">$99.99</span>
                                    </div>
                                    
                                    <div class="bg-gray-700 rounded-lg p-4 mb-6">
                                        <div class="flex flex-col sm:flex-row gap-4">
                                            <div class="flex-shrink-0 w-full sm:w-32 h-32 bg-gray-600 rounded-lg flex items-center justify-center">
                                                <svg class="h-16 w-16 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                                                </svg>
                                            </div>
                                            <div class="flex-grow">
                                                <h3 class="text-white font-medium">Premium Laptop Pro</h3>
                                                <p class="text-gray-400 text-sm mb-3">High-performance laptop with 16GB RAM and 512GB SSD storage.</p>
                                                <div class="flex space-x-2">
                                                    <button onclick="viewProduct('laptop-pro-1')" class="px-3 py-1.5 bg-primary hover:bg-primary-dark text-white rounded-md text-sm transition-colors">
                                                        View Details
                                                    </button>
                                                    <button onclick="addToCart('laptop-pro-1')" class="px-3 py-1.5 bg-gray-600 hover:bg-gray-500 text-white rounded-md text-sm transition-colors">
                                                        Add to Cart
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="bg-gray-700 rounded-lg p-4">
                                        <h3 class="text-white font-medium mb-3">Subscribe to Newsletter</h3>
                                        <form onsubmit="submitForm(event, 'newsletter')">
                                            <div class="flex flex-col sm:flex-row gap-3">
                                                <input type="email" placeholder="Enter your email" class="px-3 py-2 bg-gray-800 border border-gray-600 rounded-md flex-grow text-gray-300 focus:outline-none focus:border-primary-light">
                                                <button type="submit" class="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-md transition-colors">
                                                    Subscribe
                                                </button>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Custom Event Generator -->
                        <div class="bg-dark-lighter rounded-lg border border-gray-700 overflow-hidden">
                            <div class="px-4 py-3 border-b border-gray-700">
                                <h2 class="font-medium text-white">Custom Event Generator</h2>
                            </div>
                            <div class="p-4">
                                <form id="event-generator-form" onsubmit="generateCustomEvent(event)">
                                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                        <div>
                                            <label class="block text-sm text-gray-400 mb-1">Event Name</label>
                                            <input type="text" id="event-name" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-gray-300 focus:outline-none focus:border-primary-light" placeholder="e.g., button_click" required>
                                        </div>
                                        <div>
                                            <label class="block text-sm text-gray-400 mb-1">Event Category</label>
                                            <select id="event-category" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-gray-300 focus:outline-none focus:border-primary-light">
                                                <option value="interaction">Interaction</option>
                                                <option value="navigation">Navigation</option>
                                                <option value="conversion">Conversion</option>
                                                <option value="engagement">Engagement</option>
                                                <option value="error">Error</option>
                                                <option value="custom">Custom</option>
                                            </select>
                                        </div>
                                    </div>
                                    
                                    <div class="mb-4">
                                        <label class="block text-sm text-gray-400 mb-1">Event Properties (JSON)</label>
                                        <textarea id="event-properties" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-gray-300 focus:outline-none focus:border-primary-light h-24 font-mono" placeholder='{"property": "value", "number": 123}'>{"source": "custom_generator"}</textarea>
                                    </div>
                                    
                                    <div class="flex justify-between items-center">
                                        <div>
                                            <label class="inline-flex items-center">
                                                <input type="checkbox" id="include-user-id" class="bg-gray-800 border-gray-700 rounded text-primary-light focus:ring-primary-light">
                                                <span class="ml-2 text-sm text-gray-300">Include User ID</span>
                                            </label>
                                        </div>
                                        <button type="submit" class="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-md transition-colors">
                                            Send Event
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                        
                        <!-- Event Stream Simulation -->
                        <div class="bg-dark-lighter rounded-lg border border-gray-700 overflow-hidden">
                            <div class="px-4 py-3 border-b border-gray-700 flex justify-between items-center">
                                <h2 class="font-medium text-white">Event Stream Simulation</h2>
                                <div class="flex items-center">
                                    <label class="inline-flex items-center mr-3">
                                        <input type="checkbox" id="auto-events" class="bg-gray-800 border-gray-700 rounded text-primary-light focus:ring-primary-light">
                                        <span class="ml-2 text-sm text-gray-300">Auto Generate</span>
                                    </label>
                                    <select id="event-frequency" class="px-2 py-1 bg-gray-800 border border-gray-700 rounded-md text-gray-300 text-sm focus:outline-none focus:border-primary-light">
                                        <option value="slow">Slow (10-20s)</option>
                                        <option value="medium" selected>Medium (5-10s)</option>
                                        <option value="fast">Fast (2-5s)</option>
                                    </select>
                                </div>
                            </div>
                            <div class="p-4">
                                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
                                    <button onclick="simulateEvent('page_view')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Page View
                                    </button>
                                    <button onclick="simulateEvent('button_click')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Button Click
                                    </button>
                                    <button onclick="simulateEvent('form_submit')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Form Submit
                                    </button>
                                    <button onclick="simulateEvent('product_view')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Product View
                                    </button>
                                    <button onclick="simulateEvent('add_to_cart')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Add to Cart
                                    </button>
                                    <button onclick="simulateEvent('checkout')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Checkout
                                    </button>
                                    <button onclick="simulateEvent('purchase')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Purchase
                                    </button>
                                    <button onclick="simulateEvent('signup')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Sign Up
                                    </button>
                                    <button onclick="simulateEvent('login')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Login
                                    </button>
                                    <button onclick="simulateEvent('error')" class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md text-sm text-gray-300 transition-colors">
                                        Error
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Event Monitor Panel -->
                    <div class="space-y-6">
                        <!-- Status Card -->
                        <div class="bg-dark-lighter rounded-lg border border-gray-700 overflow-hidden">
                            <div class="px-4 py-3 border-b border-gray-700">
                                <h2 class="font-medium text-white">Connection Status</h2>
                            </div>
                            <div class="p-4">
                                <div class="grid grid-cols-2 gap-4 mb-4">
                                    <div class="bg-gray-800 p-3 rounded-lg border border-gray-700">
                                        <div class="text-xs text-gray-400 mb-1">Project ID</div>
                                        <div class="text-sm text-white font-mono truncate" id="status-project-id">{{ tracking_id if tracking_id else "Not set" }}</div>
                                    </div>
                                    <div class="bg-gray-800 p-3 rounded-lg border border-gray-700">
                                        <div class="text-xs text-gray-400 mb-1">API Status</div>
                                        <div class="text-sm text-white" id="status-api">
                                            <span class="inline-flex items-center">
                                                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-primary-light" fill="none" viewBox="0 0 24 24">
                                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                                Checking...
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <div class="grid grid-cols-2 gap-4">
                                    <div class="bg-gray-800 p-3 rounded-lg border border-gray-700">
                                        <div class="text-xs text-gray-400 mb-1">User ID</div>
                                        <div class="flex items-center">
                                            <input type="text" id="user-id-input" class="w-full px-2 py-1 bg-gray-900 border border-gray-700 rounded-l-md text-sm text-gray-300 focus:outline-none focus:border-primary-light" placeholder="Enter User ID">
                                            <button onclick="setUserId()" class="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded-r-md border border-gray-700 transition-colors">Set</button>
                                        </div>
                                    </div>
                                    <div class="bg-gray-800 p-3 rounded-lg border border-gray-700">
                                        <div class="text-xs text-gray-400 mb-1">Last Event</div>
                                        <div class="text-sm text-white" id="status-last-event">None</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Event Log -->
                        <div class="bg-dark-lighter rounded-lg border border-gray-700 overflow-hidden">
                            <div class="px-4 py-3 border-b border-gray-700 flex justify-between items-center">
                                <h2 class="font-medium text-white">Event Log</h2>
                                <button onclick="clearEventLog()" class="px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-md text-xs transition-colors">
                                    Clear Log
                                </button>
                            </div>
                            <div class="p-4">
                                <div id="event-log" class="bg-gray-900 rounded-lg border border-gray-700 p-4 h-96 overflow-y-auto font-mono text-sm">
                                    <div class="text-gray-500 text-center">No events logged yet</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- API Responses -->
                        <div class="bg-dark-lighter rounded-lg border border-gray-700 overflow-hidden">
                            <div class="px-4 py-3 border-b border-gray-700">
                                <h2 class="font-medium text-white">API Responses</h2>
                            </div>
                            <div class="p-4">
                                <div id="api-responses" class="bg-gray-900 rounded-lg border border-gray-700 p-4 max-h-60 overflow-y-auto font-mono text-sm">
                                    <div class="text-gray-500 text-center">No API responses yet</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
        
        <!-- Footer -->
        <footer class="bg-dark-lighter border-t border-gray-700 py-4 px-6">
            <div class="max-w-6xl mx-auto flex justify-between items-center">
                <div class="text-sm text-gray-400">
                    Test Analytics - Running on port {{ port }}
                </div>
                <div class="text-sm text-gray-400">
                    <span id="event-count">0</span> events sent
                </div>
            </div>
        </footer>
        
        <!-- Event Indicator -->
        <div id="event-indicator" class="fixed bottom-4 right-4 bg-primary text-white px-3 py-2 rounded-lg shadow-lg hidden z-10">
            <div class="flex items-center">
                <svg class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
                <span id="event-indicator-text">Event Sent</span>
            </div>
        </div>
    </div>
    
    <script>
        // Variables
        let eventCount = 0;
        let autoEventsInterval = null;
        let currentPage = '/home';
        let currentUserId = null;
        
        // DOM Elements
        const connectionStatus = document.getElementById('connection-status');
        const connectionText = document.getElementById('connection-text');
        const statusProjectId = document.getElementById('status-project-id');
        const statusApi = document.getElementById('status-api');
        const statusLastEvent = document.getElementById('status-last-event');
        const eventLog = document.getElementById('event-log');
        const apiResponses = document.getElementById('api-responses');
        const eventIndicator = document.getElementById('event-indicator');
        const eventIndicatorText = document.getElementById('event-indicator-text');
        const eventCountElement = document.getElementById('event-count');
        const userIdInput = document.getElementById('user-id-input');
        const autoEventsCheckbox = document.getElementById('auto-events');
        const eventFrequencySelect = document.getElementById('event-frequency');
        
        // Check API connection
        function checkApiConnection() {
            fetch('{{ api_test_endpoint }}')
                .then(response => {
                    if (response.ok) {
                        connectionStatus.classList.remove('bg-yellow-500', 'bg-red-500');
                        connectionStatus.classList.add('bg-green-500');
                        connectionText.textContent = 'Connected';
                        connectionText.classList.remove('text-gray-400', 'text-red-400');
                        connectionText.classList.add('text-green-400');
                        
                        statusApi.innerHTML = '<span class="text-green-400">Connected</span>';
                    } else {
                        throw new Error('API responded with status: ' + response.status);
                    }
                })
                .catch(error => {
                    console.error('API connection error:', error);
                    connectionStatus.classList.remove('bg-yellow-500', 'bg-green-500');
                    connectionStatus.classList.add('bg-red-500');
                    connectionText.textContent = 'Connection Error';
                    connectionText.classList.remove('text-gray-400', 'text-green-400');
                    connectionText.classList.add('text-red-400');
                    
                    statusApi.innerHTML = '<span class="text-red-400">Error</span>';
                });
        }
        
        // Set user ID
        function setUserId() {
            const userId = userIdInput.value.trim();
            if (userId) {
                if (window.ProductAnalytics) {
                    window.ProductAnalytics.setUserId(userId);
                    currentUserId = userId;
                    userIdInput.value = '';
                    
                    // Log event
                    logEvent({
                        type: 'user_set',
                        userId: userId,
                        timestamp: new Date().toISOString()
                    });
                }
            }
        }
        
        // Navigate to a page
        function navigate(page) {
            currentPage = page;
            // Track page view
            if (window.ProductAnalytics) {
                window.ProductAnalytics.track('page_view', {
                    page: page,
                    referrer: currentPage
                });
            }
            
            // Update status
            logEvent({
                type: 'navigation',
                page: page,
                timestamp: new Date().toISOString()
            });
        }
        
        // View product
        function viewProduct(productId) {
            if (window.ProductAnalytics) {
                window.ProductAnalytics.track('product_view', {
                    product_id: productId,
                    page: currentPage
                });
            }
        }
        
        // Add to cart
        function addToCart(productId) {
            if (window.ProductAnalytics) {
                window.ProductAnalytics.track('add_to_cart', {
                    product_id: productId,
                    page: currentPage,
                    quantity: 1,
                    price: 99.99
                });
            }
        }
        
        // Submit form
        function submitForm(event, formType) {
            event.preventDefault();
            
            if (window.ProductAnalytics) {
                window.ProductAnalytics.track('form_submit', {
                    form_type: formType,
                    page: currentPage
                });
            }
            
            // Show success message
            alert('Form submitted successfully!');
        }
        
        // Simulate an event
        function simulateEvent(eventType) {
            if (window.ProductAnalytics) {
                let properties = {
                    page: currentPage,
                    source: 'simulator'
                };
                
                // Add specific properties based on event type
                switch(eventType) {
                    case 'page_view':
                        properties.referrer = 'https://www.google.com';
                        properties.title = 'Page Title';
                        break;
                    case 'button_click':
                        properties.button_id = 'btn-' + Math.floor(Math.random() * 100);
                        properties.button_text = 'Click Me';
                        break;
                    case 'form_submit':
                        properties.form_id = 'form-' + Math.floor(Math.random() * 10);
                        properties.form_name = 'contact-form';
                        break;
                    case 'product_view':
                        properties.product_id = 'prod-' + Math.floor(Math.random() * 1000);
                        properties.product_name = 'Sample Product';
                        properties.category = 'Electronics';
                        properties.price = 99.99;
                        break;
                    case 'add_to_cart':
                        properties.product_id = 'prod-' + Math.floor(Math.random() * 1000);
                        properties.product_name = 'Sample Product';
                        properties.quantity = 1;
                        properties.price = 99.99;
                        break;
                    case 'checkout':
                        properties.cart_id = 'cart-' + Math.floor(Math.random() * 100);
                        properties.items = 2;
                        properties.total = 199.98;
                        break;
                    case 'purchase':
                        properties.order_id = 'order-' + Math.floor(Math.random() * 1000);
                        properties.total = 199.98;
                        properties.currency = 'USD';
                        break;
                    case 'signup':
                        properties.method = 'email';
                        properties.plan = 'free';
                        break;
                    case 'login':
                        properties.method = 'email';
                        properties.success = true;
                        break;
                    case 'error':
                        properties.error_type = 'validation';
                        properties.error_message = 'Invalid input';
                        properties.error_code = 400;
                        break;
                }
                
                window.ProductAnalytics.track(eventType, properties);
            }
        }
        
        // Generate custom event
        function generateCustomEvent(event) {
            event.preventDefault();
            
            const eventName = document.getElementById('event-name').value;
            const eventCategory = document.getElementById('event-category').value;
            const eventPropertiesText = document.getElementById('event-properties').value;
            const includeUserId = document.getElementById('include-user-id').checked;
            
            try {
                // Parse properties
                let properties = JSON.parse(eventPropertiesText);
                
                // Add category
                properties.category = eventCategory;
                
                // Set user ID if needed
                if (includeUserId && currentUserId) {
                    if (window.ProductAnalytics) {
                        window.ProductAnalytics.setUserId(currentUserId);
                    }
                } else if (!includeUserId && currentUserId) {
                    // Clear user ID
                    if (window.ProductAnalytics) {
                        window.ProductAnalytics.setUserId(null);
                    }
                }
                
                // Track the event
                if (window.ProductAnalytics) {
                    window.ProductAnalytics.track(eventName, properties);
                }
                
                // Reset form (but keep properties)
                document.getElementById('event-name').value = '';
                
            } catch (error) {
                console.error('Error parsing JSON properties:', error);
                alert('Invalid JSON properties. Please check your format.');
            }
        }
        
        // Log event to the UI
        function logEvent(eventData) {
            // Clear placeholder if this is the first event
            if (eventLog.innerHTML.includes('No events logged yet')) {
                eventLog.innerHTML = '';
            }
            
            // Create event entry
            const eventEntry = document.createElement('div');
            eventEntry.className = 'mb-2 pb-2 border-b border-gray-800';
            
            // Format timestamp
            const timestamp = new Date(eventData.timestamp);
            const formattedTime = timestamp.toLocaleTimeString();
            
            // Determine event type color
            let typeColor = 'text-blue-400';
            if (eventData.type === 'event_tracked') typeColor = 'text-green-400';
            if (eventData.type === 'event_sent') typeColor = 'text-purple-400';
            if (eventData.type === 'api_response') typeColor = 'text-yellow-400';
            if (eventData.type === 'user_set') typeColor = 'text-indigo-400';
            if (eventData.type === 'navigation') typeColor = 'text-red-400';
            
            // Create event header
            const eventHeader = document.createElement('div');
            eventHeader.className = 'flex justify-between items-center';
            eventHeader.innerHTML = `
                <span class="${typeColor}">${eventData.type || 'unknown'}</span>
                <span class="text-gray-500 text-xs">${formattedTime}</span>
            `;
            eventEntry.appendChild(eventHeader);
            
            // Create event details
            if (eventData.eventData) {
                const eventDetails = document.createElement('div');
                eventDetails.className = 'mt-1 text-xs';
                
                const eventName = eventData.eventData.event_name;
                const userId = eventData.eventData.user_id || 'anonymous';
                
                eventDetails.innerHTML = `
                    <span class="text-gray-400">Name: </span>
                    <span class="text-white">${eventName}</span>
                    <span class="mx-1 text-gray-600">|</span>
                    <span class="text-gray-400">User: </span>
                    <span class="text-white">${userId}</span>
                `;
                eventEntry.appendChild(eventDetails);
            }
            
            // Special handling for different event types
            if (eventData.type === 'navigation') {
                const navDetails = document.createElement('div');
                navDetails.className = 'mt-1 text-xs';
                navDetails.innerHTML = `
                    <span class="text-gray-400">Page: </span>
                    <span class="text-white">${eventData.page}</span>
                `;
                eventEntry.appendChild(navDetails);
            }
            
            if (eventData.type === 'user_set') {
                const userDetails = document.createElement('div');
                userDetails.className = 'mt-1 text-xs';
                userDetails.innerHTML = `
                    <span class="text-gray-400">User ID: </span>
                    <span class="text-white">${eventData.userId}</span>
                `;
                eventEntry.appendChild(userDetails);
            }
            
            if (eventData.type === 'api_response') {
                const responseDetails = document.createElement('div');
                responseDetails.className = 'mt-1 text-xs';
                responseDetails.innerHTML = `
                    <span class="text-gray-400">Status: </span>
                    <span class="${eventData.success ? 'text-green-400' : 'text-red-400'}">${eventData.success ? 'Success' : 'Error'}</span>
                `;
                eventEntry.appendChild(responseDetails);
            }
            
            // Add to log
            eventLog.insertBefore(eventEntry, eventLog.firstChild);
            
            // Update last event status
            if (eventData.type === 'event_tracked' && eventData.eventData) {
                statusLastEvent.textContent = eventData.eventData.event_name;
            }
            
            // Update API responses section for API responses
            if (eventData.type === 'api_response') {
                // Clear placeholder if this is the first response
                if (apiResponses.innerHTML.includes('No API responses yet')) {
                    apiResponses.innerHTML = '';
                }
                
                const responseEntry = document.createElement('div');
                responseEntry.className = 'mb-2 pb-2 border-b border-gray-800';
                
                const responseHeader = document.createElement('div');
                responseHeader.className = 'flex justify-between items-center';
                responseHeader.innerHTML = `
                    <span class="${eventData.success ? 'text-green-400' : 'text-red-400'}">API Response</span>
                    <span class="text-gray-500 text-xs">${formattedTime}</span>
                `;
                responseEntry.appendChild(responseHeader);
                
                if (eventData.data) {
                    const responseData = document.createElement('div');
                    responseData.className = 'mt-1 text-xs';
                    
                    // Pretty format JSON
                    const jsonString = JSON.stringify(eventData.data, null, 2);
                    const highlightedJson = syntaxHighlight(jsonString);
                    
                    responseData.innerHTML = highlightedJson;
                    responseEntry.appendChild(responseData);
                }
                
                apiResponses.insertBefore(responseEntry, apiResponses.firstChild);
            }
        }
        
        // Syntax highlight JSON
        function syntaxHighlight(json) {
            json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
                let cls = 'text-blue-400'; // number
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'text-yellow-400'; // key
                        match = match.replace(':', '');
                    } else {
                        cls = 'text-green-400'; // string
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'text-purple-400'; // boolean
                } else if (/null/.test(match)) {
                    cls = 'text-red-400'; // null
                }
                return '<span class="' + cls + '">' + match + '</span>';
            });
        }
        
        // Show event indicator
        function showEventIndicator(text) {
            eventIndicator.classList.remove('hidden', 'send-event');
            eventIndicatorText.textContent = text;
            
            // Add send animation
            setTimeout(() => {
                eventIndicator.classList.add('send-event');
            }, 10);
            
            // Hide after animation
            setTimeout(() => {
                eventIndicator.classList.add('hidden');
                eventIndicator.classList.remove('send-event');
            }, 2000);
        }
        
        // Clear event log
        function clearEventLog() {
            eventLog.innerHTML = '<div class="text-gray-500 text-center">No events logged yet</div>';
            apiResponses.innerHTML = '<div class="text-gray-500 text-center">No API responses yet</div>';
        }
        
        // Auto generate events
        function toggleAutoEvents() {
            if (autoEventsCheckbox.checked) {
                startAutoEvents();
            } else {
                stopAutoEvents();
            }
        }
        
        function startAutoEvents() {
            if (autoEventsInterval) {
                clearInterval(autoEventsInterval);
            }
            
            autoEventsInterval = setInterval(() => {
                // Pick a random event type
                const eventTypes = [
                    'page_view', 'button_click', 'form_submit', 
                    'product_view', 'add_to_cart', 'checkout', 
                    'purchase', 'signup', 'login'
                ];
                const randomEvent = eventTypes[Math.floor(Math.random() * eventTypes.length)];
                
                // Simulate the event
                simulateEvent(randomEvent);
                
            }, getRandomDelay());
        }
        
        function stopAutoEvents() {
            if (autoEventsInterval) {
                clearInterval(autoEventsInterval);
                autoEventsInterval = null;
            }
        }
        
        function getRandomDelay() {
            const frequency = eventFrequencySelect.value;
            
            switch(frequency) {
                case 'slow':
                    return Math.floor(Math.random() * (20000 - 10000)) + 10000; // 10-20 seconds
                case 'medium':
                    return Math.floor(Math.random() * (10000 - 5000)) + 5000; // 5-10 seconds
                case 'fast':
                    return Math.floor(Math.random() * (5000 - 2000)) + 2000; // 2-5 seconds
                default:
                    return 5000;
            }
        }
        
        // Event listeners
        document.addEventListener('analytics-event-tracked', function(e) {
            eventCount++;
            eventCountElement.textContent = eventCount;
            
            logEvent({
                type: 'event_tracked',
                eventData: e.detail.eventData,
                timestamp: new Date().toISOString()
            });
            
            showEventIndicator('Event Tracked: ' + e.detail.eventData.event_name);
        });
        
        document.addEventListener('analytics-event-sent', function(e) {
            logEvent({
                type: 'event_sent',
                eventData: e.detail.eventData,
                success: e.detail.success,
                status: e.detail.status,
                timestamp: new Date().toISOString()
            });
            
            // Make API request to get response data
            fetch('{{ api_endpoint }}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(e.detail.eventData)
            })
            .then(response => response.json())
            .then(data => {
                logEvent({
                    type: 'api_response',
                    success: e.detail.success,
                    data: data,
                    timestamp: new Date().toISOString()
                });
            })
            .catch(error => {
                console.error('Error fetching API response:', error);
            });
        });
        
        document.addEventListener('analytics-user-set', function(e) {
            currentUserId = e.detail.userId;
        });
        
        autoEventsCheckbox.addEventListener('change', toggleAutoEvents);
        eventFrequencySelect.addEventListener('change', function() {
            if (autoEventsCheckbox.checked) {
                stopAutoEvents();
                startAutoEvents();
            }
        });
        
        // Initialize
        window.onload = function() {
            checkApiConnection();
            
            // Check connection status periodically
            setInterval(checkApiConnection, 30000);
            
            // Initial page view
            if (window.ProductAnalytics) {
                setTimeout(() => {
                    window.ProductAnalytics.track('page_view', {
                        page: '/home',
                        referrer: 'direct',
                        title: 'Analytics Test Page'
                    });
                }, 1000);
            }
        };
    </script>
</body>
</html>
"""

# Create the HTML template file
with open(os.path.join(os.path.dirname(__file__), 'templates', 'test_analytics.html'), 'w') as f:
    f.write(index_html)

# Routes
@app.route('/')
def index():
    return redirect(url_for('test_page_selector'))

@app.route('/test')
def test_page_selector():
    """Page to select a project to test"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Analytics Test Selector</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            /* Dark Theme Adjustments */
            body {
                background-color: #1e1e2d;
                color: #f3f4f6;
            }
            
            .card-hover:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            }
        </style>
    </head>
    <body class="bg-gray-900 text-gray-200 min-h-screen">
        <div class="min-h-screen flex flex-col">
            <header class="bg-gray-800 border-b border-gray-700 py-4 px-6">
                <div class="max-w-6xl mx-auto">
                    <div class="flex items-center">
                        <svg class="h-8 w-8 text-indigo-400 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                        <div>
                            <h1 class="text-xl font-bold text-white">Analytics Test Page</h1>
                            <p class="text-sm text-gray-400">Select a project to test</p>
                        </div>
                    </div>
                </div>
            </header>
            
            <main class="flex-grow p-6">
                <div class="max-w-6xl mx-auto">
                    <div class="bg-gray-800 rounded-lg shadow-md border border-gray-700 overflow-hidden">
                        <div class="px-6 py-4 border-b border-gray-700">
                            <h2 class="text-lg font-semibold text-white">Choose a Project to Test</h2>
                        </div>
                        <div class="p-6">
                            <form action="/test/connect" method="get" class="mb-6">
                                <div class="mb-4">
                                    <label for="tracking_id" class="block text-sm font-medium text-gray-300 mb-1">Project Tracking ID</label>
                                    <div class="flex">
                                        <input type="text" id="tracking_id" name="tracking_id" 
                                            class="bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-l-lg focus:ring-indigo-500 focus:border-indigo-500 block w-full p-2.5" 
                                            placeholder="Enter your project tracking ID" required>
                                        <button type="submit" 
                                            class="text-white bg-indigo-600 hover:bg-indigo-700 focus:ring-4 focus:outline-none focus:ring-indigo-300 font-medium rounded-r-lg text-sm px-5 py-2.5 text-center">
                                            Connect
                                        </button>
                                    </div>
                                    <p class="mt-1 text-sm text-gray-400">Enter the tracking ID from your project details page</p>
                                </div>
                            </form>
                            
                            <div class="bg-gray-900 p-4 rounded-lg border border-gray-700 mb-4">
                                <div class="flex items-start">
                                    <svg class="h-5 w-5 text-blue-400 mt-0.5 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                    <div>
                                        <h3 class="text-white font-medium">What is the Test Page?</h3>
                                        <p class="text-gray-400 mt-1 text-sm">This test page allows you to simulate user interactions and events on your website. You can use it to verify that your analytics tracking is working correctly and to debug any issues.</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="bg-gray-900 p-4 rounded-lg border border-gray-700">
                                    <h3 class="font-medium text-white mb-2">With this test page you can:</h3>
                                    <ul class="text-gray-400 text-sm list-disc list-inside space-y-1">
                                        <li>Simulate user navigation and interactions</li>
                                        <li>Create custom events with properties</li>
                                        <li>Monitor API responses in real-time</li>
                                        <li>Test your analytics implementation</li>
                                        <li>Generate sample data for your dashboard</li>
                                    </ul>
                                </div>
                                
                                <div class="bg-gray-900 p-4 rounded-lg border border-gray-700">
                                    <h3 class="font-medium text-white mb-2">Getting Started:</h3>
                                    <ol class="text-gray-400 text-sm list-decimal list-inside space-y-1">
                                        <li>Enter your project tracking ID above</li>
                                        <li>Click "Connect" to open the test page</li>
                                        <li>Use the demo website to simulate events</li>
                                        <li>Check your project analytics to see the events</li>
                                        <li>Verify that events are being tracked correctly</li>
                                    </ol>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
            
            <footer class="bg-gray-800 border-t border-gray-700 py-4 px-6">
                <div class="max-w-6xl mx-auto">
                    <div class="text-sm text-gray-400">
                        Test Analytics - Running on port {{ port }}
                    </div>
                </div>
            </footer>
        </div>
    </body>
    </html>
    """, port=PORT, main_app_url=MAIN_APP_URL)

@app.route('/test/connect')
def test_connect():
    """Connect to a project for testing"""
    tracking_id = request.args.get('tracking_id')
    if not tracking_id:
        return redirect(url_for('test_page_selector'))
    
    return redirect(url_for('test_page', tracking_id=tracking_id))

@app.route('/test/<tracking_id>')
def test_page(tracking_id):
    """Test page for analytics with a specific tracking ID"""
    return render_template('test_analytics.html',
                          tracking_id=tracking_id,
                          project_id="1",  # This would normally be looked up
                          api_endpoint=API_ENDPOINT,
                          api_test_endpoint=API_TEST_ENDPOINT,
                          main_app_url=MAIN_APP_URL,
                          port=PORT)

@app.route('/api/test-event', methods=['POST'])
def test_event():
    """Endpoint to test event tracking"""
    try:
        data = request.json
        events.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'data': data
        })
        return jsonify({"status": "success", "message": "Event recorded"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all recorded events"""
    return jsonify(events)

if __name__ == '__main__':
    print(f"Starting test website on http://localhost:{PORT}")
    print(f"Visit http://localhost:{PORT}/test to select a project to test")
    app.run(host='0.0.0.0', port=PORT, debug=True)