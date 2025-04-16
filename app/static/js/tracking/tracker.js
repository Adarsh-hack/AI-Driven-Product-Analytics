/**
 * Product Analytics Tracker
 * A lightweight script to track user activity and send events to the analytics server
 */

(function(window, document) {
    'use strict';
    
    // Configuration
    const config = {
        apiEndpoint: '{{API_ENDPOINT}}',
        projectId: '{{PROJECT_ID}}',
        trackPageviews: true,
        trackClicks: true,
        trackForms: true,
        sessionTimeout: 30, // minutes
        debug: false
    };
    
    // Initialize tracker
    const tracker = {
        // Store visitor data
        visitor: {
            id: null,
            sessionId: null,
            referrer: document.referrer,
            userAgent: navigator.userAgent,
            language: navigator.language,
            screenSize: `${window.screen.width}x${window.screen.height}`,
            viewportSize: `${window.innerWidth}x${window.innerHeight}`
        },
        
        /**
         * Initialize the tracker
         */
        init: function() {
            // Set visitor ID (generate or get from storage)
            this.visitor.id = this.getVisitorId();
            this.visitor.sessionId = this.getSessionId();
            
            // Log initialization in debug mode
            this.debug('Tracker initialized', this.visitor);
            
            // Track initial pageview
            if (config.trackPageviews) {
                this.trackPageview();
                
                // Track pageview on history changes (SPA support)
                window.addEventListener('popstate', () => this.trackPageview());
                
                // Track SPA navigation by monkey-patching history methods
                const originalPushState = history.pushState;
                const originalReplaceState = history.replaceState;
                
                history.pushState = function() {
                    originalPushState.apply(this, arguments);
                    tracker.trackPageview();
                };
                
                history.replaceState = function() {
                    originalReplaceState.apply(this, arguments);
                    tracker.trackPageview();
                };
            }
            
            // Track clicks
            if (config.trackClicks) {
                document.addEventListener('click', event => this.handleClick(event));
            }
            
            // Track form submissions
            if (config.trackForms) {
                document.addEventListener('submit', event => this.handleFormSubmit(event));
            }
            
            // Track unload/visibility
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'hidden') {
                    this.trackEvent('visibility', 'tab_hidden');
                } else if (document.visibilityState === 'visible') {
                    this.trackEvent('visibility', 'tab_visible');
                }
            });
            
            // Track window unload
            window.addEventListener('beforeunload', () => {
                this.trackEvent('page', 'exit');
            });
            
            // Animation to show tracker is active (debug mode only)
            if (config.debug) {
                const debugIndicator = document.createElement('div');
                debugIndicator.innerHTML = '📊';
                debugIndicator.style.position = 'fixed';
                debugIndicator.style.bottom = '10px';
                debugIndicator.style.right = '10px';
                debugIndicator.style.zIndex = '9999';
                debugIndicator.style.background = 'rgba(0,0,0,0.6)';
                debugIndicator.style.color = '#4CC9F0';
                debugIndicator.style.padding = '5px 8px';
                debugIndicator.style.borderRadius = '4px';
                debugIndicator.style.fontSize = '18px';
                debugIndicator.style.transition = 'all 0.3s ease';
                debugIndicator.title = 'Product Analytics Tracker Active';
                
                document.body.appendChild(debugIndicator);
                
                debugIndicator.addEventListener('click', () => {
                    this.debug('Active tracking events:', this._lastEvents);
                });
                
                // Pulse animation
                setInterval(() => {
                    debugIndicator.style.transform = 'scale(1.2)';
                    setTimeout(() => {
                        debugIndicator.style.transform = 'scale(1)';
                    }, 300);
                }, 5000);
            }
        },
        
        /**
         * Track a pageview
         */
        trackPageview: function() {
            const data = {
                url: window.location.href,
                path: window.location.pathname,
                title: document.title,
                referrer: document.referrer
            };
            
            this.send('pageview', data);
        },
        
        /**
         * Track a custom event
         * @param {string} category - Event category
         * @param {string} action - Event action
         * @param {object} data - Additional data to send
         */
        trackEvent: function(category, action, data = {}) {
            const eventData = {
                category,
                action,
                ...data
            };
            
            this.send('event', eventData);
        },
        
        /**
         * Handle click tracking
         * @param {Event} event - Click event
         */
        handleClick: function(event) {
            const target = event.target.closest('a, button, [role="button"], input[type="button"], input[type="submit"]');
            
            if (!target) return;
            
            // Get element data
            let elementData = {
                type: target.tagName.toLowerCase(),
                text: target.innerText || target.value || ''
            };
            
            // Link specific tracking
            if (target.tagName === 'A') {
                elementData.href = target.href;
                
                // Track as external if it points to a different domain
                const isExternal = target.hostname !== window.location.hostname;
                if (isExternal) {
                    elementData.external = true;
                }
                
                // Track as download if it has download attribute or matches common file extensions
                const isDownload = target.hasAttribute('download') || 
                                  /\.(pdf|zip|rar|tar|gz|dmg|exe|mp4|mp3|csv|xls|xlsx|doc|docx)$/i.test(target.href);
                if (isDownload) {
                    elementData.download = true;
                }
            }
            
            // Get ID, classes and data attributes
            if (target.id) elementData.id = target.id;
            if (target.className && typeof target.className === 'string') elementData.className = target.className;
            
            // Get data attributes
            const dataTrack = target.getAttribute('data-track');
            if (dataTrack) elementData.dataTrack = dataTrack;
            
            // Track the click
            this.trackEvent('click', elementData.type, elementData);
        },
        
        /**
         * Handle form submission tracking
         * @param {Event} event - Form submit event
         */
        handleFormSubmit: function(event) {
            const form = event.target;
            
            // Get form data for tracking
            const formData = {
                id: form.id || null,
                action: form.action,
                method: form.method,
                fields: form.elements.length
            };
            
            // Add form name if available
            if (form.name) formData.name = form.name;
            
            // Track the form submission
            this.trackEvent('form', 'submit', formData);
        },
        
        /**
         * Send data to the analytics server
         * @param {string} type - Event type
         * @param {object} data - Event data
         */
        send: function(type, data) {
            // Build payload
            const payload = {
                type,
                projectId: config.projectId,
                timestamp: new Date().toISOString(),
                url: window.location.href,
                visitor: this.visitor,
                data
            };
            
            // Store event for debugging
            if (config.debug) {
                if (!this._lastEvents) this._lastEvents = [];
                this._lastEvents.push(payload);
                if (this._lastEvents.length > 10) this._lastEvents.shift();
            }
            
            // Log in debug mode
            this.debug(`Sending ${type}`, payload);
            
            // Send data using Beacon API if supported, fallback to fetch
            if (navigator.sendBeacon) {
                navigator.sendBeacon(
                    config.apiEndpoint,
                    JSON.stringify(payload)
                );
            } else {
                fetch(config.apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload),
                    // Use keepalive to ensure the request completes even on page unload
                    keepalive: true
                }).catch(error => {
                    this.debug('Error sending data', error);
                });
            }
        },
        
        /**
         * Get or generate visitor ID
         * @returns {string} Visitor ID
         */
        getVisitorId: function() {
            // Try to get visitor ID from localStorage
            let visitorId = localStorage.getItem('pa_visitor_id');
            
            // If not found, generate a new one
            if (!visitorId) {
                visitorId = this.generateId();
                localStorage.setItem('pa_visitor_id', visitorId);
            }
            
            return visitorId;
        },
        
        /**
         * Get or generate session ID
         * @returns {string} Session ID
         */
        getSessionId: function() {
            // Get current session data
            let sessionData = JSON.parse(sessionStorage.getItem('pa_session') || '{}');
            const now = new Date().getTime();
            
            // Check if session exists and is valid
            if (sessionData.id && sessionData.lastActivity) {
                // Check if session has expired
                const sessionAge = now - sessionData.lastActivity;
                const sessionTimeout = config.sessionTimeout * 60 * 1000; // Convert minutes to ms
                
                if (sessionAge > sessionTimeout) {
                    // Session expired, create new one
                    sessionData = {
                        id: this.generateId(),
                        lastActivity: now,
                        pageviews: 0
                    };
                } else {
                    // Update last activity
                    sessionData.lastActivity = now;
                    sessionData.pageviews = (sessionData.pageviews || 0) + 1;
                }
            } else {
                // No session, create new one
                sessionData = {
                    id: this.generateId(),
                    lastActivity: now,
                    pageviews: 1
                };
            }
            
            // Save session data
            sessionStorage.setItem('pa_session', JSON.stringify(sessionData));
            
            return sessionData.id;
        },
        
        /**
         * Generate a unique ID
         * @returns {string} Unique ID
         */
        generateId: function() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        },
        
        /**
         * Log debug messages
         */
        debug: function() {
            if (!config.debug) return;
            console.log('📊 Product Analytics:', ...arguments);
        }
    };
    
    // Initialize the tracker
    tracker.init();
    
    // Expose tracker object for public API
    window.ProductAnalytics = {
        /**
         * Track a custom event
         * @param {string} category - Event category
         * @param {string} action - Event action
         * @param {object} data - Additional data
         */
        trackEvent: function(category, action, data) {
            tracker.trackEvent(category, action, data);
        },
        
        /**
         * Track a pageview
         */
        trackPageview: function() {
            tracker.trackPageview();
        },
        
        /**
         * Enable debug mode
         */
        enableDebug: function() {
            config.debug = true;
            tracker.debug('Debug mode enabled');
        },
        
        /**
         * Get visitor ID
         * @returns {string} Visitor ID
         */
        getVisitorId: function() {
            return tracker.visitor.id;
        }
    };
})(window, document);