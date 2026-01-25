# LendFlow Documentation

Welcome to the LendFlow documentation directory. This folder contains all technical documentation for the LendFlow lending management platform.

## 📚 Documentation Index

### Deployment

- **[EC2 Deployment Guide](deployment/EC2_DEPLOYMENT_GUIDE.md)** - Complete step-by-step guide for deploying LendFlow on AWS EC2 Ubuntu server
- **[Quick Reference](deployment/QUICK_REFERENCE.md)** - Quick reference for common deployment commands and troubleshooting
- **[Initial Setup Script](deployment/deploy_initial_setup.sh)** - Automated bash script for initial EC2 server setup

## 🚀 Getting Started

### For Developers

1. Review the main [README.md](../README.md) in the project root
2. Check [WORKFLOWS.md](../WORKFLOWS.md) for common development workflows

### For Deployment

1. Start with the [EC2 Deployment Guide](deployment/EC2_DEPLOYMENT_GUIDE.md)
2. Use the [Quick Reference](deployment/QUICK_REFERENCE.md) for daily operations
3. Run the [deployment script](deployment/deploy_initial_setup.sh) to automate initial setup

## 📂 Documentation Structure

```
docs/
├── README.md                           # This file
└── deployment/                         # Deployment documentation
    ├── EC2_DEPLOYMENT_GUIDE.md        # Full deployment guide
    ├── QUICK_REFERENCE.md             # Command reference
    └── deploy_initial_setup.sh        # Setup automation script
```

## 🔍 Quick Links

### Deployment Topics

- [EC2 Instance Setup](deployment/EC2_DEPLOYMENT_GUIDE.md#step-1-ec2-instance-setup)
- [PostgreSQL Configuration](deployment/EC2_DEPLOYMENT_GUIDE.md#step-4-postgresql-database-setup)
- [Gunicorn Setup](deployment/EC2_DEPLOYMENT_GUIDE.md#step-6-gunicorn-configuration)
- [Nginx Configuration](deployment/EC2_DEPLOYMENT_GUIDE.md#step-7-nginx-web-server-setup)
- [SSL with Let's Encrypt](deployment/EC2_DEPLOYMENT_GUIDE.md#step-8-ssl-certificate-lets-encrypt)
- [Troubleshooting Guide](deployment/EC2_DEPLOYMENT_GUIDE.md#troubleshooting)

### Quick Commands

- [Application Updates](deployment/QUICK_REFERENCE.md#application-updates)
- [Service Management](deployment/QUICK_REFERENCE.md#service-management)
- [Database Management](deployment/QUICK_REFERENCE.md#database-management)
- [Logs and Debugging](deployment/QUICK_REFERENCE.md#logs-and-debugging)

## 📝 Contributing to Documentation

When adding new documentation:

1. Place files in appropriate subdirectories
2. Update this README with links to new documents
3. Use clear, descriptive filenames
4. Follow the existing markdown formatting style
5. Include code examples where applicable

## 🆘 Need Help?

- **Deployment Issues**: Check the [Troubleshooting section](deployment/EC2_DEPLOYMENT_GUIDE.md#troubleshooting)
- **Common Problems**: See [Common Issues](deployment/QUICK_REFERENCE.md#common-issues)
- **GitHub Repository**: [LendFlow on GitHub](https://github.com/jossieT/LendFlow)

---

**Last Updated**: January 2026
