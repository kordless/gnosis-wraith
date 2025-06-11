#!/usr/bin/env python3
"""
Comprehensive Company Test URLs for OCR Crawl Testing
Based on the SemanticStorageEngine crawler examples, with focus on:
- Logging/monitoring companies like Splunk and Loggly  
- Analytics and data visualization companies
- Security and DevOps platforms
- Companies with rich visual content good for OCR testing
"""

# Test URL categories organized by industry and visual content richness
TEST_COMPANY_URLS = {
    "logging_and_monitoring": {
        "description": "Companies specializing in log management, monitoring, and observability",
        "ocr_value": "High - dashboards, charts, metrics visualizations",
        "urls": [
            {"url": "https://www.splunk.com", "title": "Splunk", "collections": ["logging", "analytics", "enterprise"]},
            {"url": "https://www.loggly.com", "title": "Loggly", "collections": ["logging", "cloud", "saas"]},
            {"url": "https://www.elastic.co", "title": "Elastic (ELK Stack)", "collections": ["search", "logging", "analytics"]},
            {"url": "https://www.datadog.com", "title": "Datadog", "collections": ["monitoring", "apm", "cloud"]},
            {"url": "https://newrelic.com", "title": "New Relic", "collections": ["apm", "monitoring", "performance"]},
            {"url": "https://www.dynatrace.com", "title": "Dynatrace", "collections": ["apm", "ai", "monitoring"]},
            {"url": "https://grafana.com", "title": "Grafana", "collections": ["visualization", "monitoring", "opensource"]},
            {"url": "https://prometheus.io", "title": "Prometheus", "collections": ["monitoring", "metrics", "opensource"]},
            {"url": "https://www.sumologic.com", "title": "Sumo Logic", "collections": ["logging", "cloud", "security"]},
            {"url": "https://www.fluentd.org", "title": "Fluentd", "collections": ["logging", "opensource", "data_collection"]},
            {"url": "https://logz.io", "title": "Logz.io", "collections": ["logging", "elk", "cloud"]},
            {"url": "https://www.papertrail.com", "title": "Papertrail", "collections": ["logging", "cloud", "simple"]},
        ]
    },
    
    "analytics_and_bi": {
        "description": "Business intelligence, analytics, and data visualization platforms",
        "ocr_value": "Very High - charts, graphs, dashboards, infographics",
        "urls": [
            {"url": "https://www.tableau.com", "title": "Tableau", "collections": ["visualization", "bi", "analytics"]},
            {"url": "https://powerbi.microsoft.com", "title": "Microsoft Power BI", "collections": ["microsoft", "bi", "analytics"]},
            {"url": "https://looker.com", "title": "Looker (Google Cloud)", "collections": ["google", "bi", "cloud"]},
            {"url": "https://www.qlik.com", "title": "Qlik", "collections": ["visualization", "bi", "enterprise"]},
            {"url": "https://www.sisense.com", "title": "Sisense", "collections": ["bi", "analytics", "ai"]},
            {"url": "https://www.domo.com", "title": "Domo", "collections": ["cloud", "bi", "analytics"]},
            {"url": "https://chartio.com", "title": "Chartio", "collections": ["visualization", "cloud", "simple"]},
            {"url": "https://www.metabase.com", "title": "Metabase", "collections": ["opensource", "bi", "simple"]},
            {"url": "https://superset.apache.org", "title": "Apache Superset", "collections": ["apache", "opensource", "visualization"]},
        ]
    },
    
    "cybersecurity": {
        "description": "Security platforms and threat intelligence companies",
        "ocr_value": "High - security dashboards, threat maps, incident reports", 
        "urls": [
            {"url": "https://www.crowdstrike.com", "title": "CrowdStrike", "collections": ["security", "endpoint", "ai"]},
            {"url": "https://www.sentinelone.com", "title": "SentinelOne", "collections": ["security", "ai", "endpoint"]},
            {"url": "https://www.darktrace.com", "title": "Darktrace", "collections": ["security", "ai", "network"]},
            {"url": "https://www.vectra.ai", "title": "Vectra AI", "collections": ["security", "ai", "network"]},
            {"url": "https://www.cylance.com", "title": "Cylance", "collections": ["security", "ai", "endpoint"]},
            {"url": "https://www.paloaltonetworks.com", "title": "Palo Alto Networks", "collections": ["security", "firewall", "enterprise"]},
            {"url": "https://www.fortinet.com", "title": "Fortinet", "collections": ["security", "network", "enterprise"]},
            {"url": "https://www.checkpoint.com", "title": "Check Point", "collections": ["security", "firewall", "enterprise"]},
            {"url": "https://www.fireeye.com", "title": "FireEye", "collections": ["security", "threat_intelligence", "enterprise"]},
            {"url": "https://www.rapid7.com", "title": "Rapid7", "collections": ["security", "vulnerability", "analytics"]},
        ]
    },
    
    "devops_and_cloud": {
        "description": "DevOps platforms, CI/CD, and cloud infrastructure companies",
        "ocr_value": "Medium-High - pipeline visualizations, infrastructure diagrams",
        "urls": [
            {"url": "https://www.jenkins.io", "title": "Jenkins", "collections": ["devops", "ci_cd", "opensource"]},
            {"url": "https://about.gitlab.com", "title": "GitLab", "collections": ["devops", "git", "ci_cd"]},
            {"url": "https://github.com", "title": "GitHub", "collections": ["git", "microsoft", "development"]},
            {"url": "https://www.docker.com", "title": "Docker", "collections": ["containers", "devops", "platform"]},
            {"url": "https://kubernetes.io", "title": "Kubernetes", "collections": ["containers", "orchestration", "cncf"]},
            {"url": "https://www.hashicorp.com", "title": "HashiCorp", "collections": ["infrastructure", "devops", "automation"]},
            {"url": "https://www.ansible.com", "title": "Ansible", "collections": ["automation", "configuration", "redhat"]},
            {"url": "https://puppet.com", "title": "Puppet", "collections": ["automation", "configuration", "enterprise"]},
            {"url": "https://www.chef.io", "title": "Chef", "collections": ["automation", "configuration", "enterprise"]},
            {"url": "https://aws.amazon.com", "title": "Amazon Web Services", "collections": ["cloud", "aws", "amazon"]},
        ]
    },
    
    "enterprise_software": {
        "description": "Large enterprise software platforms with complex UIs",
        "ocr_value": "High - complex enterprise dashboards, workflow diagrams",
        "urls": [
            {"url": "https://www.salesforce.com", "title": "Salesforce", "collections": ["crm", "cloud", "enterprise"]},
            {"url": "https://www.oracle.com", "title": "Oracle", "collections": ["database", "enterprise", "cloud"]},
            {"url": "https://www.sap.com", "title": "SAP", "collections": ["erp", "enterprise", "business"]},
            {"url": "https://www.microsoft.com", "title": "Microsoft", "collections": ["enterprise", "cloud", "productivity"]},
            {"url": "https://www.ibm.com", "title": "IBM", "collections": ["enterprise", "ai", "cloud"]},
            {"url": "https://www.workday.com", "title": "Workday", "collections": ["hr", "finance", "cloud"]},
            {"url": "https://www.servicenow.com", "title": "ServiceNow", "collections": ["itsm", "workflow", "enterprise"]},
            {"url": "https://www.atlassian.com", "title": "Atlassian", "collections": ["productivity", "development", "enterprise"]},
        ]
    },
    
    "fintech_and_trading": {
        "description": "Financial technology and trading platforms",
        "ocr_value": "Very High - trading charts, financial dashboards, market data",
        "urls": [
            {"url": "https://www.bloomberg.com/professional", "title": "Bloomberg Terminal", "collections": ["finance", "trading", "data"]},
            {"url": "https://www.refinitiv.com", "title": "Refinitiv", "collections": ["finance", "data", "trading"]},
            {"url": "https://www.tradingview.com", "title": "TradingView", "collections": ["trading", "charts", "analysis"]},
            {"url": "https://www.interactivebrokers.com", "title": "Interactive Brokers", "collections": ["trading", "brokerage", "platform"]},
            {"url": "https://www.td.com", "title": "TD Ameritrade", "collections": ["trading", "brokerage", "retail"]},
            {"url": "https://www.schwab.com", "title": "Charles Schwab", "collections": ["trading", "investment", "retail"]},
            {"url": "https://stripe.com", "title": "Stripe", "collections": ["payments", "fintech", "api"]},
            {"url": "https://square.com", "title": "Square", "collections": ["payments", "pos", "fintech"]},
            {"url": "https://www.paypal.com", "title": "PayPal", "collections": ["payments", "fintech", "consumer"]},
        ]
    },
    
    "visual_content_rich": {
        "description": "Companies with visually rich websites ideal for OCR testing",
        "ocr_value": "Maximum - infographics, embedded charts, visual content",
        "urls": [
            {"url": "https://www.adobe.com", "title": "Adobe", "collections": ["design", "creative", "visual"]},
            {"url": "https://www.canva.com", "title": "Canva", "collections": ["design", "visual", "templates"]},
            {"url": "https://www.figma.com", "title": "Figma", "collections": ["design", "collaboration", "ui_ux"]},
            {"url": "https://dribbble.com", "title": "Dribbble", "collections": ["design", "portfolio", "creative"]},
            {"url": "https://99designs.com", "title": "99designs", "collections": ["design", "marketplace", "creative"]},
            {"url": "https://www.shutterstock.com", "title": "Shutterstock", "collections": ["stock_media", "visual", "content"]},
            {"url": "https://unsplash.com", "title": "Unsplash", "collections": ["photography", "free", "visual"]},
            {"url": "https://www.pinterest.com", "title": "Pinterest", "collections": ["visual", "discovery", "social"]},
        ]
    }
}

# Simple test configurations for different scenarios
SIMPLE_TEST_CONFIGS = {
    "quick_logging_test": [
        "https://www.splunk.com",
        "https://www.loggly.com", 
        "https://www.datadog.com",
        "https://grafana.com"
    ],
    
    "visual_heavy_test": [
        "https://www.tableau.com",
        "https://www.tradingview.com",
        "https://www.adobe.com",
        "https://dribbble.com"
    ],
    
    "enterprise_dashboard_test": [
        "https://www.salesforce.com",
        "https://www.servicenow.com",
        "https://www.crowdstrike.com",
        "https://newrelic.com"
    ]
}

def get_test_urls(category=None, limit=None):
    """
    Get test URLs for OCR crawl testing
    
    Args:
        category: Specific category to get URLs from, or None for all
        limit: Maximum number of URLs to return
    
    Returns:
        List of URL dictionaries with metadata
    """
    urls = []
    
    if category and category in TEST_COMPANY_URLS:
        # Get URLs from specific category
        category_data = TEST_COMPANY_URLS[category]
        urls = category_data["urls"]
    else:
        # Get URLs from all categories
        for cat_name, cat_data in TEST_COMPANY_URLS.items():
            for url_info in cat_data["urls"]:
                # Add category info to each URL
                url_with_category = url_info.copy()
                url_with_category["category"] = cat_name
                url_with_category["ocr_value"] = cat_data["ocr_value"]
                urls.append(url_with_category)
    
    # Apply limit if specified
    if limit:
        urls = urls[:limit]
    
    return urls

def get_simple_test_config(config_name):
    """Get a simple list of URLs for quick testing"""
    return SIMPLE_TEST_CONFIGS.get(config_name, [])

def print_test_categories():
    """Print available test categories and their descriptions"""
    print("🎯 Available Test Categories:")
    print("="*60)
    
    for category, data in TEST_COMPANY_URLS.items():
        print(f"\n📂 {category.upper().replace('_', ' ')}")
        print(f"   📝 {data['description']}")
        print(f"   🔍 OCR Value: {data['ocr_value']}")
        print(f"   📊 URLs: {len(data['urls'])} companies")

def print_simple_configs():
    """Print available simple test configurations"""
    print("\n⚡ Quick Test Configurations:")
    print("="*40)
    
    for config_name, urls in SIMPLE_TEST_CONFIGS.items():
        print(f"\n🚀 {config_name}")
        print(f"   📊 {len(urls)} URLs")
        for url in urls:
            print(f"   • {url}")

if __name__ == "__main__":
    print("🕷️ OCR Crawl Test URL Database")
    print_test_categories()
    print_simple_configs()
    
    print(f"\n📊 Total URLs available: {sum(len(cat['urls']) for cat in TEST_COMPANY_URLS.values())}")
    print("\n🔍 Example usage:")
    print("  from test_company_urls import get_test_urls, get_simple_test_config")
    print("  urls = get_test_urls('logging_and_monitoring', limit=5)")
    print("  quick_urls = get_simple_test_config('quick_logging_test')")
