"""Security helpers.

Legacy shared-secret X-Service-Token validation has been removed. Protected
routes use app.middleware.service_auth.require_service_token, which validates
short-lived internal bearer tokens issued by orchestrator.
"""
