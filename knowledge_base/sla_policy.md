# Service Level Agreement (SLA) Policy

## Overview
SenAI provides the following SLA guarantees to all paid subscription customers.

## Uptime Guarantees

| Plan | Monthly Uptime SLA | Downtime Allowed |
|------|-------------------|-----------------|
| Starter | 99.0% | 7.2 hours/month |
| Professional | 99.5% | 3.6 hours/month |
| Enterprise | 99.9% | 43.2 min/month |

## Incident Severity Levels

### P1 - Critical (System Down)
- **Definition**: Complete service unavailability affecting all customers
- **Response SLA**: 15 minutes
- **Resolution SLA**: 4 hours
- **Communication**: Every 30 minutes via status page

### P2 - High (Major Degradation)
- **Definition**: Core features unavailable for >25% of customers
- **Response SLA**: 1 hour
- **Resolution SLA**: 8 hours

### P3 - Medium (Partial Degradation)
- **Definition**: Non-critical features affected or minor performance issues
- **Response SLA**: 4 hours
- **Resolution SLA**: 24 hours

### P4 - Low (Minor Issues)
- **Definition**: Cosmetic issues, minor bugs with workarounds available
- **Response SLA**: 1 business day
- **Resolution SLA**: 5 business days

## SLA Credit Calculation

When SenAI fails to meet the SLA, customers are entitled to service credits:

| Uptime | Credit |
|--------|--------|
| 99.0% - 99.49% | 10% of monthly fee |
| 98.0% - 98.99% | 25% of monthly fee |
| 95.0% - 97.99% | 50% of monthly fee |
| Below 95.0% | 100% of monthly fee |

## Credit Request Process
1. Customer must request SLA credits within **30 days** of the incident
2. Submit request to: sla-credits@senai.io with incident reference
3. Credits are applied to next invoice within **2 billing cycles**
4. Maximum credit per month: 100% of monthly subscription fee

## Exclusions
SLA credits do not apply for:
- Scheduled maintenance windows (announced 72+ hours in advance)
- Force majeure events (natural disasters, acts of war)
- Customer-caused outages or misconfigurations
- Beta or preview features
- Free tier usage

## Planned Maintenance
- Maintenance windows: Sundays 02:00-06:00 UTC
- Advanced notice: Minimum **72 hours** for planned maintenance
- Emergency maintenance: Maximum **2 hours** notice

## Enterprise SLA Addendum
Enterprise customers may negotiate custom SLA terms including:
- Dedicated incident response team
- Custom RTO/RPO requirements
- Financial penalties beyond service credits
