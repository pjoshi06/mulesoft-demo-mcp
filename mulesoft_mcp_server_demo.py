#!/usr/bin/env python3
"""
MCP Server for MuleSoft Anypoint Platform CLI commands
Designed for incident management and troubleshooting workflows

This server provides tools for:
- Application monitoring and management
- API management and troubleshooting
- Runtime diagnostics
- Performance analysis
- Incident remediation
"""
import subprocess
import json
import os
from typing import Any, Optional
from fastmcp import FastMCP
from datetime import datetime, timedelta

# Initialize the MCP server
mcp = FastMCP("MuleSoft Anypoint Platform Server")

# Mock mode enabled by default for demo purposes
# Set MULESOFT_MOCK_MODE=false to connect to real Anypoint Platform
MOCK_MODE = os.getenv("MULESOFT_MOCK_MODE", "true").lower() == "true"

# ============================================================================
# APPLICATION MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def list_applications(environment: str = "Production") -> str:
    """
    List all deployed Mule applications in an environment
    
    Args:
        environment: Environment name (e.g., Production, Staging, Development)
    """
    if MOCK_MODE:
        return json.dumps({
            "applications": [
                {
                    "name": "customer-api",
                    "status": "STARTED",
                    "environment": environment,
                    "workers": 2,
                    "workerType": "MICRO",
                    "region": "us-east-1",
                    "lastModified": "2026-02-10T14:30:00Z",
                    "muleVersion": "4.4.0"
                },
                {
                    "name": "payment-processor",
                    "status": "STARTED",
                    "environment": environment,
                    "workers": 4,
                    "workerType": "SMALL",
                    "region": "us-east-1",
                    "lastModified": "2026-02-12T09:15:00Z",
                    "muleVersion": "4.4.0"
                },
                {
                    "name": "order-fulfillment-api",
                    "status": "FAILED",
                    "environment": environment,
                    "workers": 2,
                    "workerType": "MICRO",
                    "region": "us-west-2",
                    "lastModified": "2026-02-14T08:00:00Z",
                    "muleVersion": "4.3.0",
                    "errorMessage": "Application failed to start due to configuration error"
                },
                {
                    "name": "inventory-sync-service",
                    "status": "STARTED",
                    "environment": environment,
                    "workers": 1,
                    "workerType": "MICRO",
                    "region": "us-east-1",
                    "lastModified": "2026-01-28T11:20:00Z",
                    "muleVersion": "4.4.0"
                },
                {
                    "name": "oauth-authentication-experience-api",
                    "status": "STARTED",
                    "environment": environment,
                    "workers": 2,
                    "workerType": "SMALL",
                    "region": "us-east-1",
                    "lastModified": "2026-02-14T18:35:00Z",
                    "muleVersion": "4.4.0",
                    "statusReason": "High error rate - 504 Gateway Timeout from downstream Cognito"
                },
                {
                    "name": "cards-sca-business-api",
                    "status": "STARTED",
                    "environment": environment,
                    "workers": 3,
                    "workerType": "MICRO",
                    "region": "us-east-1",
                    "lastModified": "2026-02-10T09:00:00Z",
                    "muleVersion": "4.4.0",
                    "statusReason": "Experiencing intermittent failures due to OAuth token issues"
                }
            ],
            "total": 6
        }, indent=2)
    
    try:
        # Real command would use anypoint-cli
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "list",
             "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def describe_application(app_name: str, environment: str = "Production") -> str:
    """
    Get detailed information about a specific Mule application
    
    Args:
        app_name: Name of the application
        environment: Environment name
    """
    if MOCK_MODE:
        # Simulate different states for demo
        if app_name == "order-fulfillment-api":
            status = "FAILED"
            error_info = {
                "errorMessage": "Application failed to start",
                "errorDetails": "Configuration property 'db.host' is missing",
                "lastDeployment": {
                    "status": "FAILED",
                    "timestamp": "2026-02-14T08:00:00Z",
                    "deployedBy": "admin@company.com"
                }
            }
        else:
            status = "STARTED"
            error_info = {}
        
        return json.dumps({
            "application": {
                "name": app_name,
                "status": status,
                "environment": environment,
                "domain": f"{app_name}.us-e1.cloudhub.io",
                "workers": {
                    "amount": 2,
                    "type": {
                        "name": "MICRO",
                        "weight": 0.1,
                        "cpu": "0.1 vCores",
                        "memory": "500 MB"
                    }
                },
                "region": "us-east-1",
                "muleVersion": "4.4.0",
                "lastModified": "2026-02-14T08:00:00Z",
                "properties": {
                    "http.port": "8081",
                    "anypoint.platform.client_id": "***masked***",
                    "anypoint.platform.client_secret": "***masked***"
                },
                "runtime": {
                    "javaVersion": "1.8.0_345",
                    "staticIpsEnabled": False,
                    "persistentQueues": True
                },
                **error_info
            }
        }, indent=2)
    
    try:
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "describe",
             app_name, "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def get_application_logs(app_name: str, environment: str = "Production", 
                         tail_lines: int = 100) -> str:
    """
    Get recent application logs for troubleshooting
    
    Args:
        app_name: Name of the application
        environment: Environment name
        tail_lines: Number of recent log lines to retrieve (default 100)
    """
    if MOCK_MODE:
        # Simulate different log patterns for different apps
        if app_name == "oauth-authentication-experience-api":
            logs = [
                "2024-09-06T18:35:07.628Z INFO [[MuleRuntime].uber.15: [oauth-authentication-experience-api].oauth-authentication-exp-11ef-8a7b-0ab70e1f9a09] org.mule.runtime.core.internal.processor.LoggerMessageProcessor: {",
                '  "Correlation ID": "8feb64fb-ce26-42b9-a37c-1d0774cba23d",',
                '  "Transaction ID": "8feb64fb-ce26-42b9-a37c-1d0774cba23d",',
                '  "Application Name": "API Gateway OAuth2 Experience API",',
                '  "Date Time Stamp": "2024-09-06T18:35:07.628Z",',
                '  "type": "ERROR",',
                '  "status_code": 504,',
                '  "action": "ERROR RESPONSE SENT",',
                '  "Headers": {',
                '    "x-api-transaction-id": "ca1b58b2-c34f-4af2-9bf2-fe247f13c56e",',
                '    "x-api-correlation-id": "5bcfadd8-919a-4d76-8b43-44ddbaa061e9",',
                '    "x-ratelimit-remaining": "24",',
                '    "x-ratelimit-limit": "25",',
                '    "x-ratelimit-reset": "857"',
                "  }",
                "}",
                "2024-09-06T18:35:08.145Z ERROR Cognito System API returned timeout after 5000ms",
                "2024-09-06T18:35:08.146Z WARN Rate limit approaching - 24 of 25 requests remaining",
                "2024-09-06T18:36:12.334Z ERROR [[MuleRuntime].uber.15] Gateway timeout - Unable to obtain access token from Cognito",
                "2024-09-06T18:36:12.335Z ERROR Cards SCA authentication flow failed - access token generation timeout",
                "2024-09-06T18:37:45.221Z INFO Retry attempt 1/3 for access token generation",
                "2024-09-06T18:37:50.445Z ERROR Retry failed - Cognito System API still timing out"
            ]
        elif app_name == "cards-sca-business-api":
            logs = [
                "2024-09-06T18:34:00.123Z INFO Processing Cards SCA eCommerce transaction request",
                "2024-09-06T18:34:00.450Z INFO Calling OAuth authentication experience API for token",
                "2024-09-06T18:34:05.678Z ERROR OAuth API returned 504 - Gateway Timeout",
                "2024-09-06T18:34:05.679Z ERROR Unable to authenticate user - access token unavailable",
                "2024-09-06T18:34:05.680Z WARN Transaction failed - returning error to customer",
                "2024-09-06T18:35:30.123Z INFO Retry transaction attempt",
                "2024-09-06T18:35:35.890Z ERROR OAuth API still failing - 504 Gateway Timeout",
                "2024-09-06T18:36:00.234Z WARN Failure rate increased to 12% in last 30 minutes",
                "2024-09-06T18:36:00.235Z ERROR Customer impact: Unable to process debit card transaction",
                "2024-09-06T18:36:00.236Z ERROR Customer impact: Unable to process credit card transaction"
            ]
        elif app_name == "order-fulfillment-api":
            logs = [
                "2026-02-14 08:00:15 ERROR [main] org.mule.runtime.core.internal.context.DefaultMuleContext: Error starting application",
                "2026-02-14 08:00:15 ERROR [main] org.mule.runtime.module.deployment.impl.DefaultApplicationDeployer: Failed to deploy application",
                "2026-02-14 08:00:15 ERROR [main] Configuration property 'db.host' is required but not set",
                "2026-02-14 08:00:15 FATAL [main] Application startup failed",
                "2026-02-14 08:00:16 INFO  [main] org.mule.runtime.module.deployment.impl.DefaultApplicationDeployer: Application deployment failed: order-fulfillment-api"
            ]
        elif app_name == "payment-processor":
            logs = [
                "2026-02-14 10:15:23 INFO  [http-listener-1] Received payment request ID: pay-12345",
                "2026-02-14 10:15:24 WARN  [http-listener-1] Payment gateway response time: 2500ms (threshold: 2000ms)",
                "2026-02-14 10:15:24 INFO  [http-listener-1] Payment processed successfully: pay-12345",
                "2026-02-14 10:16:05 ERROR [http-listener-2] Payment gateway timeout after 5000ms",
                "2026-02-14 10:16:05 ERROR [http-listener-2] Retrying payment request: pay-12346",
                "2026-02-14 10:16:08 INFO  [http-listener-2] Payment retry successful: pay-12346",
                "2026-02-14 10:17:12 WARN  [scheduler-1] Database connection pool: 8/10 connections in use"
            ]
        else:
            logs = [
                f"2026-02-14 10:20:00 INFO  [http-listener-1] Processing request",
                f"2026-02-14 10:20:01 INFO  [http-listener-1] Request completed successfully",
                f"2026-02-14 10:21:15 INFO  [scheduler-1] Scheduled task executed"
            ]
        
        return json.dumps({
            "applicationName": app_name,
            "environment": environment,
            "logLines": logs,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }, indent=2)
    
    try:
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "tail-logs",
             app_name, "--environment", environment, "--lines", str(tail_lines)],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

# ============================================================================
# API MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def list_apis(environment: str = "Production") -> str:
    """
    List all managed APIs in API Manager
    
    Args:
        environment: Environment name
    """
    if MOCK_MODE:
        return json.dumps({
            "apis": [
                {
                    "id": "12345",
                    "name": "Customer API",
                    "version": "v1",
                    "status": "ACTIVE",
                    "endpoint": "https://customer-api.us-e1.cloudhub.io/api/v1",
                    "instanceLabel": "customer-api-prod",
                    "assetVersion": "1.0.5",
                    "environment": environment
                },
                {
                    "id": "12346",
                    "name": "Payment API",
                    "version": "v2",
                    "status": "ACTIVE",
                    "endpoint": "https://payment-processor.us-e1.cloudhub.io/api/v2",
                    "instanceLabel": "payment-api-prod",
                    "assetVersion": "2.1.3",
                    "environment": environment
                },
                {
                    "id": "12347",
                    "name": "Order API",
                    "version": "v1",
                    "status": "INACTIVE",
                    "endpoint": "https://order-fulfillment-api.us-w2.cloudhub.io/api/v1",
                    "instanceLabel": "order-api-prod",
                    "assetVersion": "1.2.0",
                    "environment": environment
                }
            ]
        }, indent=2)
    
    try:
        result = subprocess.run(
            ["anypoint-cli", "api-mgr", "api", "list",
             "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def get_api_analytics(api_id: str, period: str = "1h", 
                      environment: str = "Production") -> str:
    """
    Get API analytics and metrics for performance monitoring
    
    Args:
        api_id: API identifier
        period: Time period (1h, 6h, 24h, 7d, 30d)
        environment: Environment name
    """
    if MOCK_MODE:
        # Simulate different metrics based on API
        if api_id == "12346":  # Payment API with issues
            return json.dumps({
                "apiId": api_id,
                "period": period,
                "metrics": {
                    "requests": {
                        "total": 45230,
                        "successful": 42150,
                        "failed": 3080,
                        "failureRate": "6.8%"
                    },
                    "responseTime": {
                        "average": 1850,
                        "p50": 1200,
                        "p95": 3500,
                        "p99": 5200,
                        "unit": "ms"
                    },
                    "errors": {
                        "timeout": 2100,
                        "serverError": 650,
                        "clientError": 330
                    },
                    "policies": {
                        "rateLimitViolations": 125,
                        "authenticationFailures": 45
                    },
                    "topEndpoints": [
                        {"path": "/api/v2/payments/process", "requests": 35000, "avgResponseTime": 2100},
                        {"path": "/api/v2/payments/validate", "requests": 8000, "avgResponseTime": 450},
                        {"path": "/api/v2/payments/status", "requests": 2230, "avgResponseTime": 180}
                    ]
                },
                "alerts": [
                    {
                        "severity": "HIGH",
                        "type": "RESPONSE_TIME_THRESHOLD",
                        "message": "Average response time exceeded 1500ms threshold",
                        "triggeredAt": "2026-02-14T09:30:00Z"
                    },
                    {
                        "severity": "MEDIUM",
                        "type": "ERROR_RATE_THRESHOLD",
                        "message": "Error rate exceeded 5% threshold",
                        "triggeredAt": "2026-02-14T10:15:00Z"
                    }
                ]
            }, indent=2)
        else:
            return json.dumps({
                "apiId": api_id,
                "period": period,
                "metrics": {
                    "requests": {
                        "total": 12450,
                        "successful": 12385,
                        "failed": 65,
                        "failureRate": "0.5%"
                    },
                    "responseTime": {
                        "average": 245,
                        "p50": 180,
                        "p95": 450,
                        "p99": 680,
                        "unit": "ms"
                    },
                    "errors": {
                        "timeout": 15,
                        "serverError": 25,
                        "clientError": 25
                    }
                }
            }, indent=2)
    
    try:
        result = subprocess.run(
            ["anypoint-cli", "api-mgr", "analytics", "query",
             "--api-id", api_id, "--period", period,
             "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def list_api_policies(api_id: str, environment: str = "Production") -> str:
    """
    List all policies applied to an API
    
    Args:
        api_id: API identifier
        environment: Environment name
    """
    if MOCK_MODE:
        return json.dumps({
            "apiId": api_id,
            "policies": [
                {
                    "policyId": "rate-limiting-1",
                    "name": "Rate Limiting",
                    "enabled": True,
                    "configuration": {
                        "rateLimits": [
                            {"timePeriodInMilliseconds": 60000, "maximumRequests": 1000}
                        ]
                    },
                    "order": 1
                },
                {
                    "policyId": "client-id-enforcement-1",
                    "name": "Client ID Enforcement",
                    "enabled": True,
                    "configuration": {
                        "credentialsOriginHasHttpBasicAuthenticationHeader": "customExpression"
                    },
                    "order": 2
                },
                {
                    "policyId": "spike-control-1",
                    "name": "Spike Control",
                    "enabled": True,
                    "configuration": {
                        "maximumRequests": 100,
                        "timePeriodInMilliseconds": 1000
                    },
                    "order": 3
                }
            ]
        }, indent=2)
    
    try:
        result = subprocess.run(
            ["anypoint-cli", "api-mgr", "policy", "list",
             "--api-id", api_id, "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

# ============================================================================
# RUNTIME DIAGNOSTICS TOOLS
# ============================================================================

@mcp.tool()
def get_application_health(app_name: str, environment: str = "Production") -> str:
    """
    Get comprehensive health check for an application
    
    Args:
        app_name: Name of the application
        environment: Environment name
    """
    if MOCK_MODE:
        if app_name == "payment-processor":
            return json.dumps({
                "applicationName": app_name,
                "environment": environment,
                "overallHealth": "DEGRADED",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "checks": {
                    "applicationStatus": {
                        "status": "HEALTHY",
                        "message": "Application is running"
                    },
                    "workerHealth": {
                        "status": "HEALTHY",
                        "workers": [
                            {"id": "worker-0", "status": "STARTED", "cpu": "45%", "memory": "68%"},
                            {"id": "worker-1", "status": "STARTED", "cpu": "52%", "memory": "71%"}
                        ]
                    },
                    "responseTime": {
                        "status": "DEGRADED",
                        "averageMs": 2100,
                        "threshold": 1500,
                        "message": "Response time exceeds acceptable threshold"
                    },
                    "errorRate": {
                        "status": "DEGRADED",
                        "rate": "6.8%",
                        "threshold": "5%",
                        "message": "Error rate above acceptable threshold"
                    },
                    "connectivity": {
                        "status": "DEGRADED",
                        "checks": [
                            {
                                "name": "Payment Gateway",
                                "status": "DEGRADED",
                                "latency": 2500,
                                "message": "High latency detected"
                            },
                            {
                                "name": "Database",
                                "status": "HEALTHY",
                                "latency": 45
                            }
                        ]
                    }
                },
                "recommendations": [
                    "Investigate payment gateway latency issues",
                    "Review error logs for timeout patterns",
                    "Consider scaling workers if load continues"
                ]
            }, indent=2)
        elif app_name == "order-fulfillment-api":
            return json.dumps({
                "applicationName": app_name,
                "environment": environment,
                "overallHealth": "CRITICAL",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "checks": {
                    "applicationStatus": {
                        "status": "FAILED",
                        "message": "Application failed to start",
                        "error": "Configuration property 'db.host' is missing"
                    },
                    "workerHealth": {
                        "status": "FAILED",
                        "workers": []
                    }
                },
                "recommendations": [
                    "Add missing configuration property 'db.host'",
                    "Redeploy application after fixing configuration"
                ]
            }, indent=2)
        else:
            return json.dumps({
                "applicationName": app_name,
                "environment": environment,
                "overallHealth": "HEALTHY",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "checks": {
                    "applicationStatus": {"status": "HEALTHY"},
                    "workerHealth": {"status": "HEALTHY"},
                    "responseTime": {"status": "HEALTHY", "averageMs": 245},
                    "errorRate": {"status": "HEALTHY", "rate": "0.5%"}
                }
            }, indent=2)
    
    try:
        # This would combine multiple API calls in real implementation
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "describe",
             app_name, "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def get_worker_diagnostics(app_name: str, worker_id: str = "worker-0",
                           environment: str = "Production") -> str:
    """
    Get detailed diagnostics for a specific worker instance
    
    Args:
        app_name: Name of the application
        worker_id: Worker identifier (e.g., worker-0, worker-1)
        environment: Environment name
    """
    if MOCK_MODE:
        return json.dumps({
            "applicationName": app_name,
            "workerId": worker_id,
            "environment": environment,
            "diagnostics": {
                "status": "STARTED",
                "uptime": "3d 14h 23m",
                "resources": {
                    "cpu": {
                        "current": "52%",
                        "average1m": "48%",
                        "average5m": "45%",
                        "average15m": "43%"
                    },
                    "memory": {
                        "used": "356 MB",
                        "total": "500 MB",
                        "percentage": "71%",
                        "heapUsed": "280 MB",
                        "heapMax": "400 MB"
                    },
                    "threads": {
                        "total": 45,
                        "active": 12,
                        "waiting": 33
                    }
                },
                "jvm": {
                    "version": "1.8.0_345",
                    "vendor": "Oracle Corporation",
                    "gcCount": 1523,
                    "gcTime": "12.5s"
                },
                "networking": {
                    "activeConnections": 24,
                    "requestsPerSecond": 15.3,
                    "bytesIn": "1.2 GB",
                    "bytesOut": "2.8 GB"
                },
                "issues": [
                    {
                        "severity": "MEDIUM",
                        "type": "HIGH_MEMORY_USAGE",
                        "message": "Memory usage at 71% - approaching threshold",
                        "recommendation": "Monitor memory usage and consider increasing worker size if sustained"
                    }
                ]
            }
        }, indent=2)
    
    try:
        # Real implementation would query CloudHub metrics API
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "describe",
             app_name, "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

# ============================================================================
# OPERATIONAL ACTIONS
# ============================================================================

@mcp.tool()
def restart_application(app_name: str, environment: str = "Production") -> str:
    """
    Restart a Mule application
    
    Args:
        app_name: Name of the application to restart
        environment: Environment name
    """
    if MOCK_MODE:
        return json.dumps({
            "status": "RESTARTING",
            "applicationName": app_name,
            "environment": environment,
            "message": f"Restart initiated for application {app_name}",
            "estimatedTime": "2-3 minutes",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }, indent=2)
    
    try:
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "restart",
             app_name, "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def deploy_application(app_name: str, artifact_path: str,
                       environment: str = "Production",
                       workers: int = 1, worker_type: str = "MICRO") -> str:
    """
    Deploy or redeploy a Mule application
    
    Args:
        app_name: Name of the application
        artifact_path: Path to the application JAR file
        environment: Environment name
        workers: Number of workers (default 1)
        worker_type: Worker size (MICRO, SMALL, MEDIUM, LARGE)
    """
    if MOCK_MODE:
        return json.dumps({
            "status": "DEPLOYING",
            "applicationName": app_name,
            "environment": environment,
            "workers": workers,
            "workerType": worker_type,
            "message": f"Deployment initiated for {app_name}",
            "estimatedTime": "3-5 minutes",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }, indent=2)
    
    try:
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "deploy",
             app_name, artifact_path,
             "--environment", environment,
             "--workers", str(workers),
             "--workerSize", worker_type],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def update_application_properties(app_name: str, properties: str,
                                  environment: str = "Production") -> str:
    """
    Update application properties (configuration)
    
    Args:
        app_name: Name of the application
        properties: JSON string of property key-value pairs
        environment: Environment name
    """
    if MOCK_MODE:
        try:
            props_dict = json.loads(properties)
            return json.dumps({
                "status": "UPDATING",
                "applicationName": app_name,
                "environment": environment,
                "updatedProperties": props_dict,
                "message": "Configuration update initiated - application will restart",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }, indent=2)
        except json.JSONDecodeError:
            return json.dumps({
                "error": "Invalid JSON format for properties"
            }, indent=2)
    
    try:
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "modify",
             app_name, "--environment", environment,
             "--property", properties],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def scale_application(app_name: str, workers: int,
                     environment: str = "Production") -> str:
    """
    Scale application by changing number of workers
    
    Args:
        app_name: Name of the application
        workers: New number of workers
        environment: Environment name
    """
    if MOCK_MODE:
        return json.dumps({
            "status": "SCALING",
            "applicationName": app_name,
            "environment": environment,
            "currentWorkers": 2,
            "targetWorkers": workers,
            "message": f"Scaling application to {workers} workers",
            "estimatedTime": "2-4 minutes",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }, indent=2)
    
    try:
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "modify",
             app_name, "--workers", str(workers),
             "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def clear_application_queues(app_name: str, environment: str = "Production") -> str:
    """
    Clear persistent queues for an application
    
    Args:
        app_name: Name of the application
        environment: Environment name
    """
    if MOCK_MODE:
        return json.dumps({
            "status": "CLEARING",
            "applicationName": app_name,
            "environment": environment,
            "message": "Persistent queues are being cleared",
            "queueStats": {
                "messagesBefore": 1247,
                "messagesCleared": 1247
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }, indent=2)
    
    try:
        # Note: This might require CloudHub API calls rather than CLI
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "clear-queues",
             app_name, "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

# ============================================================================
# ALERT AND NOTIFICATION TOOLS
# ============================================================================

@mcp.tool()
def get_active_alerts(environment: str = "Production") -> str:
    """
    Get all active alerts and notifications for the environment
    
    Args:
        environment: Environment name
    """
    if MOCK_MODE:
        return json.dumps({
            "environment": environment,
            "alerts": [
                {
                    "id": "alert-1001",
                    "severity": "CRITICAL",
                    "application": "order-fulfillment-api",
                    "type": "APPLICATION_FAILURE",
                    "message": "Application failed to start",
                    "triggeredAt": "2026-02-14T08:00:00Z",
                    "status": "ACTIVE"
                },
                {
                    "id": "alert-1002",
                    "severity": "HIGH",
                    "application": "payment-processor",
                    "type": "RESPONSE_TIME_THRESHOLD",
                    "message": "Average response time exceeded 1500ms",
                    "triggeredAt": "2026-02-14T09:30:00Z",
                    "status": "ACTIVE",
                    "details": {
                        "threshold": 1500,
                        "current": 2100,
                        "unit": "ms"
                    }
                },
                {
                    "id": "alert-1003",
                    "severity": "MEDIUM",
                    "application": "payment-processor",
                    "type": "ERROR_RATE_THRESHOLD",
                    "message": "Error rate exceeded 5%",
                    "triggeredAt": "2026-02-14T10:15:00Z",
                    "status": "ACTIVE",
                    "details": {
                        "threshold": "5%",
                        "current": "6.8%"
                    }
                },
                {
                    "id": "alert-1004",
                    "severity": "MEDIUM",
                    "application": "payment-processor",
                    "type": "HIGH_MEMORY_USAGE",
                    "message": "Worker memory usage at 71%",
                    "triggeredAt": "2026-02-14T10:45:00Z",
                    "status": "ACTIVE",
                    "worker": "worker-1"
                }
            ],
            "summary": {
                "total": 4,
                "critical": 1,
                "high": 1,
                "medium": 2,
                "low": 0
            }
        }, indent=2)
    
    try:
        # Real implementation would query Anypoint Monitoring API
        result = subprocess.run(
            ["anypoint-cli", "monitoring", "alert", "list",
             "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

# ============================================================================
# TROUBLESHOOTING SCENARIOS
# ============================================================================

@mcp.tool()
def diagnose_cards_sca_issue(environment: str = "Production") -> str:
    """
    Comprehensive diagnostic for Cards SCA access token issues
    Based on real-world incident playbook
    
    Args:
        environment: Environment name
    """
    if MOCK_MODE:
        return json.dumps({
            "incident": {
                "title": "Cards SCA Access Token Issues",
                "severity": "P2",
                "serviceImpacted": "Cards SCA",
                "customerImpact": "Users unable to perform eCommerce transactions",
                "startTime": "2024-09-06T18:30:00Z",
                "duration": "45 minutes (ongoing)"
            },
            "rootCause": {
                "primaryIssue": "AWS Cognito System API timeout",
                "secondaryIssue": "OAuth authentication experience API returning 504 errors",
                "affectedComponents": [
                    "oauth-authentication-experience-api",
                    "cards-sca-business-api",
                    "cognito-system-api (external)"
                ]
            },
            "metrics": {
                "errorRate": {
                    "current": "12%",
                    "threshold": "10%",
                    "status": "CRITICAL"
                },
                "responseTime": {
                    "oauth-api": {
                        "p50": "5200ms",
                        "p95": "timeout (>5000ms)",
                        "expected": "500-800ms"
                    }
                },
                "failedTransactions": {
                    "debit": 45,
                    "credit": 38,
                    "total": 83,
                    "last30min": True
                },
                "rateLimiting": {
                    "remaining": 24,
                    "limit": 25,
                    "resetIn": "857 seconds",
                    "status": "OK"
                }
            },
            "diagnosticChecks": {
                "cognitoSystemAPI": {
                    "status": "DEGRADED",
                    "responseTime": "5000ms+ (timeout)",
                    "errorType": "Gateway Timeout",
                    "recommendation": "Escalate to AWS Cognito team"
                },
                "oauthExperienceAPI": {
                    "status": "DEGRADED",
                    "health": "STARTED but returning errors",
                    "workers": "2/2 healthy",
                    "issue": "Downstream dependency (Cognito) failing"
                },
                "cardsSCABusinessAPI": {
                    "status": "DEGRADED",
                    "health": "STARTED but failing transactions",
                    "workers": "3/3 healthy",
                    "issue": "Cannot obtain access tokens from OAuth API"
                },
                "businessDashboard": {
                    "journeyFailures": {
                        "debitCards": "High failure rate on authentication step",
                        "creditCards": "High failure rate on authentication step"
                    },
                    "failureRate": "12%",
                    "trend": "Increasing"
                }
            },
            "testTransactions": {
                "debitTests": {
                    "attempted": 5,
                    "successful": 0,
                    "failed": 5,
                    "errorMessage": "Unable to authenticate - access token unavailable"
                },
                "creditTests": {
                    "attempted": 5,
                    "successful": 1,
                    "failed": 4,
                    "errorMessage": "504 Gateway Timeout from OAuth API"
                }
            },
            "timeline": [
                {
                    "time": "18:30:00",
                    "event": "First 504 errors detected from OAuth API",
                    "source": "Application logs"
                },
                {
                    "time": "18:32:00",
                    "event": "Error rate spike detected in APPD",
                    "metric": "Error rate increased from 2% to 8%"
                },
                {
                    "time": "18:35:00",
                    "event": "Customer complaints received",
                    "impact": "eCommerce transactions failing"
                },
                {
                    "time": "18:36:00",
                    "event": "Failure rate exceeded 10% threshold",
                    "action": "P3 ticket creation triggered"
                },
                {
                    "time": "18:38:00",
                    "event": "Cognito System API confirmed as root cause",
                    "finding": "Consistent 5000ms+ response times"
                }
            ],
            "remediationSteps": [
                {
                    "step": 1,
                    "action": "Verify Cognito System API health",
                    "status": "COMPLETED",
                    "finding": "Cognito API timing out - AWS issue suspected",
                    "owner": "AWS Cognito team"
                },
                {
                    "step": 2,
                    "action": "Check Cards SCA Business dashboard",
                    "status": "COMPLETED",
                    "finding": "Failure rate 12% on authentication journeys",
                    "tool": "Business Intelligence Dashboard"
                },
                {
                    "step": 3,
                    "action": "Perform 5 debit + 5 credit test transactions",
                    "status": "COMPLETED",
                    "result": "9/10 failed - consistent authentication errors"
                },
                {
                    "step": 4,
                    "action": "Fetch MI report for customer impact",
                    "status": "IN_PROGRESS",
                    "command": "Query MI system for failed transactions in timeframe"
                },
                {
                    "step": 5,
                    "action": "Create P3 ticket",
                    "status": "REQUIRED",
                    "reason": "Failure rate > 10% threshold",
                    "justification": "Continuous errors impacting customer transactions"
                },
                {
                    "step": 6,
                    "action": "Escalate to AWS Cognito team",
                    "status": "REQUIRED",
                    "reason": "Root cause in external dependency",
                    "priority": "HIGH"
                },
                {
                    "step": 7,
                    "action": "Implement circuit breaker (if prolonged)",
                    "status": "PENDING",
                    "reason": "Prevent cascade failures",
                    "estimatedTime": "30 minutes"
                }
            ],
            "p3TicketCriteria": {
                "scenario1": {
                    "condition": "Spike occurs and resolves",
                    "action": "Create P3 to analyze what happened",
                    "preventive": True
                },
                "scenario2": {
                    "condition": "Errors continuously coming",
                    "action": "Create P3 to quickly investigate",
                    "reactive": True,
                    "current": "THIS SCENARIO - ERRORS ONGOING"
                }
            },
            "recommendations": {
                "immediate": [
                    "Escalate to AWS Cognito support team immediately",
                    "Implement circuit breaker for OAuth API to prevent cascade failures",
                    "Enable fallback authentication mechanism if available",
                    "Increase timeout threshold temporarily (from 5s to 10s) to allow slow responses"
                ],
                "shortTerm": [
                    "Add health check endpoint for Cognito System API",
                    "Implement retry logic with exponential backoff",
                    "Set up proactive alerts for Cognito API latency",
                    "Create runbook for OAuth/Cognito failures"
                ],
                "longTerm": [
                    "Implement authentication service redundancy",
                    "Consider multi-region Cognito setup",
                    "Add caching layer for frequently used tokens",
                    "Implement graceful degradation for authentication failures"
                ]
            },
            "monitoringAlerts": {
                "existing": [
                    {
                        "name": "OAuth API Error Rate",
                        "threshold": "10%",
                        "current": "12%",
                        "status": "TRIGGERED"
                    },
                    {
                        "name": "Response Time P95",
                        "threshold": "2000ms",
                        "current": "5000ms+",
                        "status": "TRIGGERED"
                    }
                ],
                "recommended": [
                    {
                        "name": "Cognito API Health Check",
                        "threshold": "Response time > 3000ms",
                        "severity": "HIGH"
                    },
                    {
                        "name": "Cards SCA Transaction Failure Rate",
                        "threshold": "> 5%",
                        "severity": "MEDIUM"
                    },
                    {
                        "name": "Access Token Generation Failures",
                        "threshold": "> 3 failures in 5 minutes",
                        "severity": "HIGH"
                    }
                ]
            },
            "customerImpact": {
                "affectedUsers": "~500 users (estimated based on failed transactions)",
                "affectedTransactions": 83,
                "revenueImpact": "~$12,450 in failed transactions",
                "customerExperience": "Unable to complete purchases - authentication failures",
                "duration": "45 minutes (ongoing)"
            }
        }, indent=2)
    
    try:
        # In real implementation, this would aggregate data from multiple sources
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "describe",
             "cards-sca-business-api", "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def diagnose_application_failure(app_name: str, environment: str = "Production") -> str:
    """
    Comprehensive diagnostic for a failed application
    Returns root cause analysis and remediation steps
    
    Args:
        app_name: Name of the failed application
        environment: Environment name
    """
    if MOCK_MODE:
        if app_name == "order-fulfillment-api":
            return json.dumps({
                "applicationName": app_name,
                "environment": environment,
                "diagnosis": {
                    "rootCause": "MISSING_CONFIGURATION",
                    "details": "Required configuration property 'db.host' is not set",
                    "impact": "Application unable to start - service unavailable",
                    "affectedUsers": "All users attempting to access order fulfillment service"
                },
                "timeline": [
                    {
                        "timestamp": "2026-02-14T07:55:00Z",
                        "event": "Deployment initiated",
                        "user": "admin@company.com"
                    },
                    {
                        "timestamp": "2026-02-14T07:58:00Z",
                        "event": "Configuration validation failed"
                    },
                    {
                        "timestamp": "2026-02-14T08:00:00Z",
                        "event": "Application startup failed"
                    }
                ],
                "logs": [
                    "ERROR: Configuration property 'db.host' is required but not set",
                    "FATAL: Application startup failed",
                    "INFO: Application deployment failed: order-fulfillment-api"
                ],
                "remediationSteps": [
                    {
                        "step": 1,
                        "action": "Add missing configuration property",
                        "command": "update_application_properties",
                        "parameters": {
                            "app_name": app_name,
                            "properties": '{"db.host": "production-db.company.com", "db.port": "5432"}'
                        }
                    },
                    {
                        "step": 2,
                        "action": "Restart application",
                        "command": "restart_application",
                        "parameters": {
                            "app_name": app_name
                        }
                    },
                    {
                        "step": 3,
                        "action": "Verify application health",
                        "command": "get_application_health",
                        "parameters": {
                            "app_name": app_name
                        }
                    }
                ],
                "preventionRecommendations": [
                    "Implement configuration validation in CI/CD pipeline",
                    "Use environment-specific configuration management",
                    "Add pre-deployment smoke tests"
                ]
            }, indent=2)
        else:
            return json.dumps({
                "applicationName": app_name,
                "environment": environment,
                "message": "No critical failures detected for this application"
            }, indent=2)
    
    try:
        # This would be a composite operation in real implementation
        result = subprocess.run(
            ["anypoint-cli", "runtime-mgr", "cloudhub-application", "describe",
             app_name, "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool()
def diagnose_performance_issue(app_name: str, environment: str = "Production") -> str:
    """
    Analyze performance issues and provide optimization recommendations
    
    Args:
        app_name: Name of the application
        environment: Environment name
    """
    if MOCK_MODE:
        if app_name == "payment-processor":
            return json.dumps({
                "applicationName": app_name,
                "environment": environment,
                "performanceAnalysis": {
                    "overallRating": "POOR",
                    "issues": [
                        {
                            "type": "HIGH_RESPONSE_TIME",
                            "severity": "HIGH",
                            "metric": "Average response time: 2100ms",
                            "threshold": "1500ms",
                            "deviation": "+40%"
                        },
                        {
                            "type": "BACKEND_LATENCY",
                            "severity": "HIGH",
                            "metric": "Payment gateway latency: 2500ms",
                            "expectedRange": "500-1000ms",
                            "deviation": "+150%"
                        },
                        {
                            "type": "ERROR_RATE",
                            "severity": "MEDIUM",
                            "metric": "Error rate: 6.8%",
                            "threshold": "5%",
                            "primaryError": "Gateway timeout (68% of errors)"
                        }
                    ],
                    "bottlenecks": [
                        {
                            "component": "Payment Gateway Integration",
                            "impact": "High",
                            "description": "External payment gateway showing high latency and timeout rate",
                            "affectedEndpoints": ["/api/v2/payments/process", "/api/v2/payments/validate"]
                        },
                        {
                            "component": "Database Connection Pool",
                            "impact": "Medium",
                            "description": "Connection pool utilization at 80%",
                            "recommendation": "Increase pool size or optimize queries"
                        }
                    ],
                    "recommendations": [
                        {
                            "priority": "HIGH",
                            "category": "External Integration",
                            "recommendation": "Implement circuit breaker pattern for payment gateway",
                            "expectedImpact": "Reduce timeout errors by 60-80%",
                            "effort": "Medium"
                        },
                        {
                            "priority": "HIGH",
                            "category": "External Integration",
                            "recommendation": "Add request timeout configuration (3s max)",
                            "expectedImpact": "Prevent long-running requests from blocking workers",
                            "effort": "Low"
                        },
                        {
                            "priority": "MEDIUM",
                            "category": "Caching",
                            "recommendation": "Implement response caching for validation endpoints",
                            "expectedImpact": "Reduce load by 30-40%",
                            "effort": "Medium"
                        },
                        {
                            "priority": "MEDIUM",
                            "category": "Scaling",
                            "recommendation": "Scale from 2 to 4 workers during peak hours",
                            "expectedImpact": "Improve throughput and reduce queue times",
                            "effort": "Low"
                        },
                        {
                            "priority": "LOW",
                            "category": "Database",
                            "recommendation": "Increase database connection pool size",
                            "expectedImpact": "Reduce connection wait times",
                            "effort": "Low"
                        }
                    ]
                },
                "metrics": {
                    "responseTime": {
                        "current": 2100,
                        "target": 1500,
                        "p95": 3500,
                        "p99": 5200
                    },
                    "throughput": {
                        "requestsPerSecond": 12.5,
                        "peakRequestsPerSecond": 28.3
                    },
                    "resources": {
                        "cpuAverage": "48%",
                        "memoryAverage": "69%",
                        "workerUtilization": "High"
                    }
                }
            }, indent=2)
        else:
            return json.dumps({
                "applicationName": app_name,
                "environment": environment,
                "performanceAnalysis": {
                    "overallRating": "GOOD",
                    "message": "No significant performance issues detected"
                }
            }, indent=2)
    
    try:
        # This would aggregate multiple metrics in real implementation
        result = subprocess.run(
            ["anypoint-cli", "monitoring", "metrics", "query",
             "--application", app_name, "--environment", environment],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

# ============================================================================
# UTILITY TOOLS
# ============================================================================

@mcp.tool()
def execute_custom_anypoint_command(command: str) -> str:
    """
    Execute a custom Anypoint CLI command for advanced operations
    
    Args:
        command: The Anypoint CLI command to execute (without 'anypoint-cli' prefix)
                 Example: "runtime-mgr cloudhub-application list --environment Production"
    """
    if MOCK_MODE:
        return json.dumps({
            "message": "Mock mode enabled - command not executed",
            "command": command,
            "note": "Set MULESOFT_MOCK_MODE=false to execute real commands"
        }, indent=2)
    
    try:
        cmd_parts = ["anypoint-cli"] + command.split()
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except Exception as e:
        return f"Error executing command: {str(e)}"

if __name__ == "__main__":
    # Print startup info
    mode = "MOCK (Demo)" if MOCK_MODE else "LIVE (Real Anypoint Platform)"
    print("=" * 70)
    print(f"MuleSoft Anypoint Platform MCP Server")
    print(f"Mode: {mode}")
    print("=" * 70)
    
    if MOCK_MODE:
        print("⚠️  Running with simulated MuleSoft responses")
        print("   No real Anypoint Platform connection required")
        print("")
        print("📋 Demo Scenarios:")
        print("   1. order-fulfillment-api: FAILED (missing configuration)")
        print("   2. payment-processor: DEGRADED (high latency, timeouts)")
        print("   3. oauth-authentication-experience-api: DEGRADED (Cognito timeout)")
        print("   4. cards-sca-business-api: DEGRADED (OAuth token issues)")
        print("   5. customer-api: HEALTHY")
        print("   6. inventory-sync-service: HEALTHY")
        print("")
        print("🎯 Featured Incident: Cards SCA Access Token Issues")
        print("   - Service Impact: eCommerce transactions failing")
        print("   - Root Cause: AWS Cognito System API timeouts (504)")
        print("   - Error Rate: 12% (above 10% threshold)")
        print("   - Customer Impact: 83 failed transactions, ~500 users affected")
        print("   - Try: diagnose_cards_sca_issue()")
    else:
        print("✓ Will connect to real Anypoint Platform")
        print("  Ensure anypoint-cli is installed and configured")
    
    print("=" * 70)
    print("")
    
    # Run the MCP server with SSE transport for remote access
    # Render and other cloud platforms set PORT environment variable
    port = int(os.getenv("PORT", 8000))
    
    print(f"🌐 Starting MCP Server on port {port}")
    print(f"📡 Transport: SSE (Server-Sent Events)")
    print(f"🔗 Connect from Amethyst Studio or other MCP clients")
    print(f"   URL: http://0.0.0.0:{port}/sse")
    print("")
    
    # Run with SSE transport for remote access
    mcp.run(transport="sse", port=port, host="0.0.0.0")
