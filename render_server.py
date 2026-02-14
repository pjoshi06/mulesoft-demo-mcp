#!/usr/bin/env python3
"""
HTTP Wrapper for MuleSoft MCP Server
Allows the MCP server to run on Render.com or similar HTTP-based platforms
"""
from flask import Flask, request, jsonify
import os
import sys
import json
from datetime import datetime

# Import the MCP server functions
# We'll need to modify the import based on how we structure this
app = Flask(__name__)

# Simple health check endpoint for Render
@app.route('/')
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "MuleSoft MCP Server",
        "mode": "MOCK" if os.getenv("MULESOFT_MOCK_MODE", "true").lower() == "true" else "LIVE",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    })

@app.route('/info')
def info():
    """Display server information"""
    return jsonify({
        "server": "MuleSoft Anypoint Platform MCP Server",
        "description": "AI-powered incident management for MuleSoft",
        "mode": os.getenv("MULESOFT_MOCK_MODE", "true"),
        "scenarios": [
            {
                "name": "order-fulfillment-api",
                "status": "FAILED",
                "issue": "Missing configuration"
            },
            {
                "name": "payment-processor",
                "status": "DEGRADED",
                "issue": "High latency, timeouts"
            },
            {
                "name": "oauth-authentication-experience-api",
                "status": "DEGRADED",
                "issue": "Cognito timeout (504)"
            },
            {
                "name": "cards-sca-business-api",
                "status": "DEGRADED",
                "issue": "OAuth token issues"
            },
            {
                "name": "customer-api",
                "status": "HEALTHY"
            },
            {
                "name": "inventory-sync-service",
                "status": "HEALTHY"
            }
        ],
        "endpoints": {
            "/": "Health check",
            "/info": "Server information",
            "/scenarios": "List available demo scenarios",
            "/docs": "API documentation"
        }
    })

@app.route('/scenarios')
def scenarios():
    """List all available demo scenarios"""
    return jsonify({
        "scenarios": {
            "cards-sca": {
                "title": "Cards SCA Access Token Issues",
                "severity": "P2",
                "service": "Cards SCA",
                "impact": "Users unable to perform eCommerce transactions",
                "root_cause": "AWS Cognito System API timeout (504)",
                "error_rate": "12%",
                "affected_users": "~500",
                "failed_transactions": 83
            },
            "order-fulfillment": {
                "title": "Order Fulfillment API Failure",
                "severity": "P1",
                "service": "Order Fulfillment",
                "impact": "Complete service outage",
                "root_cause": "Missing configuration property 'db.host'",
                "status": "FAILED"
            },
            "payment-performance": {
                "title": "Payment Processor Performance Degradation",
                "severity": "P2",
                "service": "Payment Processing",
                "impact": "Slow transaction processing",
                "root_cause": "Payment gateway latency",
                "response_time": "2100ms (threshold: 1500ms)",
                "error_rate": "6.8%"
            }
        },
        "note": "Use MCP protocol to interact with these scenarios via Claude Desktop"
    })

@app.route('/docs')
def docs():
    """API documentation"""
    return jsonify({
        "title": "MuleSoft MCP Server API",
        "version": "1.0.0",
        "description": "HTTP endpoints for the MuleSoft MCP Server running on Render",
        "base_url": request.host_url.rstrip('/'),
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Health check endpoint",
                "response": "Server status and basic info"
            },
            {
                "path": "/info",
                "method": "GET",
                "description": "Detailed server information",
                "response": "Server details, mode, available scenarios"
            },
            {
                "path": "/scenarios",
                "method": "GET",
                "description": "List all demo scenarios",
                "response": "Available incident scenarios with details"
            },
            {
                "path": "/docs",
                "method": "GET",
                "description": "API documentation",
                "response": "This documentation"
            }
        ],
        "mcp_integration": {
            "note": "This server primarily operates via MCP (Model Context Protocol)",
            "usage": "Configure in Claude Desktop to access full MCP tools",
            "config_example": {
                "mcpServers": {
                    "mulesoft": {
                        "command": "python",
                        "args": ["path/to/mulesoft_mcp_server_demo.py"],
                        "env": {
                            "MULESOFT_MOCK_MODE": "true"
                        }
                    }
                }
            }
        },
        "demo_mode": {
            "enabled": os.getenv("MULESOFT_MOCK_MODE", "true").lower() == "true",
            "description": "Server runs with simulated data - no real MuleSoft connection required"
        }
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": ["/", "/health", "/info", "/scenarios", "/docs"]
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "error": "Internal Server Error",
        "message": str(e)
    }), 500

if __name__ == '__main__':
    # Get port from environment (Render sets PORT automatically)
    port = int(os.environ.get('PORT', 10000))
    
    # Print startup info
    mode = "MOCK (Demo)" if os.getenv("MULESOFT_MOCK_MODE", "true").lower() == "true" else "LIVE"
    print("=" * 70)
    print(f"MuleSoft MCP Server - HTTP Wrapper")
    print(f"Mode: {mode}")
    print(f"Port: {port}")
    print("=" * 70)
    print("")
    print("HTTP Endpoints available:")
    print(f"  • Health Check: http://localhost:{port}/")
    print(f"  • Server Info:  http://localhost:{port}/info")
    print(f"  • Scenarios:    http://localhost:{port}/scenarios")
    print(f"  • API Docs:     http://localhost:{port}/docs")
    print("")
    print("Note: For full MCP functionality, use Claude Desktop with MCP protocol")
    print("=" * 70)
    print("")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
