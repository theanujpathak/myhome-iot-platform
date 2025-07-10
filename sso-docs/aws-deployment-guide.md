# AWS Deployment Guide

This guide walks you through deploying the SSO system to AWS using EC2 and ECR.

## Overview

The deployment creates:
- **EC2 Instance** (t3.medium) running all services via Docker Compose
- **ECR Repository** for storing container images
- **VPC with public/private subnets** for network isolation
- **Security Groups** with minimal required access
- **Elastic IP** for consistent public access
- **IAM Roles** for secure service communication

## Prerequisites

### Local Setup
1. **AWS CLI v2** installed and configured
2. **Terraform 1.0+** installed
3. **Docker** installed and running
4. **SSH key pair** for EC2 access

### AWS Setup
1. **AWS Account** with appropriate permissions
2. **IAM User** with following policies:
   - `AmazonEC2FullAccess`
   - `AmazonECRFullAccess`
   - `AmazonVPCFullAccess`
   - `IAMFullAccess`
   - `CloudWatchFullAccess`

### Configure AWS CLI
```bash
aws configure
# Enter your Access Key ID, Secret Access Key, Region, and Output format
```

## Quick Deployment

### 1. Build and Push Images to ECR
```bash
# Build and push all application images
./aws-deployment/scripts/build-and-push.sh
```

### 2. Deploy Infrastructure
```bash
# Deploy complete infrastructure
./aws-deployment/scripts/deploy.sh deploy
```

### 3. Access Your Applications
After deployment, access your applications at:
- **Keycloak Admin**: `http://YOUR_IP/auth`
- **Main App**: `http://YOUR_IP`
- **Admin Dashboard**: `http://YOUR_IP/admin`
- **Employee Portal**: `http://YOUR_IP/portal`
- **Demo App**: `http://YOUR_IP/demo`

## Manual Deployment Steps

### Step 1: Build Container Images

```bash
# Navigate to project root
cd /path/to/sso.i4planet.com

# Build and push to ECR
./aws-deployment/scripts/build-and-push.sh -r us-east-1 -v v1.0.0
```

### Step 2: Deploy Infrastructure

```bash
# Set environment variables
export AWS_REGION="us-east-1"
export PROJECT_NAME="sso-system"
export KEYCLOAK_ADMIN_PASSWORD="your-secure-password"
export POSTGRES_PASSWORD="your-secure-db-password"

# Deploy infrastructure
./aws-deployment/scripts/deploy.sh deploy
```

### Step 3: Configure Domain (Optional)

If you have a custom domain:

1. **Update DNS Records**:
   ```bash
   # Point your domain to the Elastic IP
   # A record: yourdomain.com -> ELASTIC_IP
   ```

2. **Update Keycloak Configuration**:
   ```bash
   # SSH into the instance
   ssh -i ~/.ssh/sso-system-key ec2-user@YOUR_IP
   
   # Update environment variables
   cd /opt/sso-system
   echo "KC_HOSTNAME=yourdomain.com" >> .env
   
   # Restart services
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Architecture Details

### Infrastructure Components

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS VPC                             │
│  ┌─────────────────┐              ┌─────────────────────┐   │
│  │  Public Subnet  │              │  Private Subnet     │   │
│  │                 │              │                     │   │
│  │  ┌───────────┐  │              │  (Future expansion) │   │
│  │  │ EC2       │  │              │                     │   │
│  │  │ Instance  │  │              │                     │   │
│  │  │           │  │              │                     │   │
│  │  │ • Nginx   │  │              │                     │   │
│  │  │ • Apps    │  │              │                     │   │
│  │  │ • Keycloak│  │              │                     │   │
│  │  │ • PostgreSQL│ │              │                     │   │
│  │  └───────────┘  │              │                     │   │
│  └─────────────────┘              └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Internet Gateway │
                    └───────────────────┘
```

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      EC2 Instance                          │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │    Nginx    │   │  React Apps │   │    Node.js API  │   │
│  │   (Port 80) │───│   (Port 80) │───│   (Port 3001)   │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
│                                                             │
│  ┌─────────────┐   ┌─────────────────────────────────────┐ │
│  │  Keycloak   │   │           PostgreSQL                │ │
│  │ (Port 8080) │───│          (Port 5432)                │ │
│  └─────────────┘   └─────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

The deployment uses these key environment variables:

```bash
# Database
POSTGRES_DB=keycloak
POSTGRES_USER=keycloak
POSTGRES_PASSWORD=your-secure-password

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=your-secure-password
KC_HOSTNAME=your-domain-or-ip

# API
NODE_API_CLIENT_SECRET=your-secure-secret

# Infrastructure
AWS_REGION=us-east-1
PROJECT_NAME=sso-system
ENVIRONMENT=production
```

### Security Groups

The deployment creates security groups with these rules:

**Inbound Rules:**
- Port 80 (HTTP): 0.0.0.0/0
- Port 443 (HTTPS): 0.0.0.0/0
- Port 22 (SSH): Your IP range
- Port 8080 (Keycloak): 0.0.0.0/0

**Outbound Rules:**
- All traffic: 0.0.0.0/0

## Monitoring and Logging

### CloudWatch Integration

The deployment includes CloudWatch monitoring:

```bash
# View logs
aws logs describe-log-groups --log-group-name-prefix sso-system

# View metrics
aws cloudwatch list-metrics --namespace SSO/System
```

### Application Logs

```bash
# SSH into instance
ssh -i ~/.ssh/sso-system-key ec2-user@YOUR_IP

# View container logs
docker-compose -f /opt/sso-system/docker-compose.prod.yml logs -f

# View specific service logs
docker logs sso-keycloak
docker logs sso-api
docker logs sso-nginx
```

## Backup and Recovery

### Database Backup

```bash
# SSH into instance
ssh -i ~/.ssh/sso-system-key ec2-user@YOUR_IP

# Create database backup
docker exec sso-postgres pg_dump -U keycloak keycloak > /opt/sso-system/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup (add to crontab)
echo "0 2 * * * docker exec sso-postgres pg_dump -U keycloak keycloak > /opt/sso-system/backups/backup_\$(date +\%Y\%m\%d_\%H\%M\%S).sql" | crontab -
```

### Configuration Backup

```bash
# Backup environment and configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    /opt/sso-system/.env \
    /opt/sso-system/docker-compose.prod.yml \
    /opt/sso-system/aws-deployment/nginx/
```

## Scaling Considerations

### Vertical Scaling

```bash
# Update instance type in Terraform
cd aws-deployment/terraform
# Edit variables.tf or terraform.tfvars
# instance_type = "t3.large"  # or larger

terraform plan
terraform apply
```

### Horizontal Scaling

For high availability, consider:

1. **Application Load Balancer** with multiple EC2 instances
2. **RDS PostgreSQL** for managed database
3. **EFS** for shared file storage
4. **Auto Scaling Groups** for automatic scaling

## Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check container status
docker-compose -f /opt/sso-system/docker-compose.prod.yml ps

# Check logs
docker-compose -f /opt/sso-system/docker-compose.prod.yml logs

# Restart services
docker-compose -f /opt/sso-system/docker-compose.prod.yml restart
```

#### Cannot Access Applications
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx

# Check nginx configuration
docker exec sso-nginx nginx -t

# Check port availability
netstat -tlnp | grep :80
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker exec sso-postgres pg_isready -U keycloak

# Check database logs
docker logs sso-postgres

# Test connection
docker exec sso-postgres psql -U keycloak -d keycloak -c "SELECT 1;"
```

### Health Checks

```bash
# Application health
curl http://YOUR_IP/health

# Keycloak health
curl http://YOUR_IP/auth/health/ready

# API health
curl http://YOUR_IP/api/health

# Database health
docker exec sso-postgres pg_isready -U keycloak
```

## Security Best Practices

### Production Recommendations

1. **Change Default Passwords**:
   ```bash
   # Update .env file with secure passwords
   KEYCLOAK_ADMIN_PASSWORD=your-very-secure-password
   POSTGRES_PASSWORD=your-very-secure-db-password
   ```

2. **Restrict SSH Access**:
   ```bash
   # Update security group to allow SSH only from your IP
   aws ec2 authorize-security-group-ingress \
       --group-id sg-xxxxxxxxx \
       --protocol tcp \
       --port 22 \
       --cidr YOUR_IP/32
   ```

3. **Enable HTTPS**:
   ```bash
   # Install SSL certificate
   # Update nginx configuration for HTTPS
   # Redirect HTTP to HTTPS
   ```

4. **Regular Updates**:
   ```bash
   # Update system packages
   sudo yum update -y
   
   # Update container images
   docker-compose pull
   docker-compose up -d
   ```

## Cost Optimization

### AWS Free Tier Usage

- **EC2**: t3.medium (not free tier, but cost-effective)
- **EBS**: 20GB GP3 storage
- **Data Transfer**: Monitor outbound data transfer
- **CloudWatch**: Basic monitoring included

### Cost Monitoring

```bash
# Check current costs
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

## Cleanup

### Destroy Infrastructure

```bash
# Destroy all AWS resources
./aws-deployment/scripts/deploy.sh destroy

# Or manually with Terraform
cd aws-deployment/terraform
terraform destroy
```

### Clean Up Local Images

```bash
# Remove local Docker images
docker system prune -a

# Remove SSH keys
rm ~/.ssh/sso-system-key*
```

---

This deployment provides a production-ready SSO system on AWS with proper security, monitoring, and scalability considerations.