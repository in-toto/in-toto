# in-toto CI/CD Integration Planner

A comprehensive web-based tool to help organizations plan, visualize, and implement in-toto integration into their CI/CD pipelines.

## Overview

The in-toto CI/CD Integration Planner provides three main capabilities:

1. **Digital Twin**: Interactive visualization of your CI/CD pipeline with in-toto integration points
2. **Goal Architect**: Structured goal setting and compliance framework mapping
3. **Action Planner**: Step-by-step implementation roadmap with timelines and prerequisites

## Features

### 🔬 Digital Twin Pipeline Visualization
- **Interactive Diagrams**: Mermaid.js-powered pipeline visualization
- **Multi-Platform Support**: GitHub Actions, Jenkins, GitLab CI, Azure DevOps, CircleCI
- **Integration Points**: Clear visualization of where in-toto components integrate
- **Step Details**: Click on any step to see detailed integration information

### 🎯 Goal Architect
- **Security Objectives**: Pre-defined security goals including cryptographic signing, build verification, and supply chain attestation
- **Compliance Frameworks**: Support for SLSA, SOC2, ISO 27001, CMMC 1.0, and CMMC 2.0
- **Success Metrics**: Quantifiable metrics for each security objective
- **Timeline Planning**: Realistic implementation timelines for each goal

### 📋 Action Planner
- **Environment Configuration**: Tailored plans for development, staging, and production
- **Key Management**: Support for multiple key management strategies
- **Detailed Steps**: Comprehensive task breakdowns with duration estimates
- **Prerequisites**: Clear dependency mapping between implementation steps

## Getting Started

### Prerequisites
- Modern web browser with JavaScript enabled
- No server setup required - runs entirely in the browser

### Installation
1. Clone the in-toto repository
2. Navigate to `tools/cicd-planner/`
3. Open `index.html` in your web browser

### Usage

#### 1. Digital Twin Creation
1. Select your CI/CD tool from the dropdown
2. Enter your pipeline steps (one per line)
3. Click "Generate Digital Twin" to create the visualization
4. Click on any pipeline step to see detailed integration information

#### 2. Goal Architecture
1. Select your security goals from the available options
2. Choose applicable compliance frameworks
3. Click "Generate Goal Architecture" to create your objectives
4. Review success metrics and timelines for each goal

#### 3. Action Planning
1. Select your target environment
2. Choose your key management strategy
3. Click "Generate Action Plan" to create your implementation roadmap
4. Follow the numbered steps with their associated timelines and prerequisites

## Supported CI/CD Tools

- **GitHub Actions**: Complete workflow integration with GitHub-specific actions
- **Jenkins**: Plugin-based integration with Jenkins pipelines
- **GitLab CI**: Native GitLab CI/CD integration patterns
- **Azure DevOps**: Azure Pipelines integration with Microsoft tooling
- **CircleCI**: Orb-based integration for CircleCI workflows

## Key Management Options

- **File-based Keys**: Traditional file-based key storage with secure practices
- **Hardware Security Module (HSM)**: Enterprise-grade hardware security
- **Cloud Key Management Service**: AWS KMS, Azure Key Vault, Google Cloud KMS
- **HashiCorp Vault**: Open-source secrets management

## Compliance Frameworks

### SLSA (Supply-chain Levels for Software Artifacts)
- Level 3 compliance mapping
- Build integrity requirements
- Provenance generation standards

### SOC2 (System and Organization Controls 2)
- Security principle alignment
- Availability and confidentiality controls
- Processing integrity requirements

### ISO 27001
- Information security management system
- Risk assessment and treatment
- Continuous improvement processes

### CMMC (Cybersecurity Maturity Model Certification)
- **CMMC 1.0**: Original framework for defense contractors
- **CMMC 2.0**: Updated framework with streamlined requirements
- DoD compliance requirements mapping

## Browser Compatibility

Tested and supported on:
- Edge Version 137.0.3296.68 (Official build) (64-bit)

## Contributing

We welcome contributions to improve the CI/CD Integration Planner:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test across supported browsers
5. Submit a pull request

### Development Guidelines
- Maintain pure HTML/CSS/JavaScript approach
- Ensure responsive design compatibility
- Follow existing code style and patterns
- Include appropriate error handling
- Test interactive features thoroughly

## Troubleshooting

### Common Issues

**Mermaid diagrams not rendering**
- Ensure JavaScript is enabled
- Check browser console for errors
- Try refreshing the page

**Interactive features not working**
- Verify browser compatibility
- Disable browser extensions that might interfere
- Check for JavaScript errors in console

**Layout issues on mobile**
- The tool is responsive but optimized for desktop use
- Use landscape orientation on mobile devices for best experience

## Security Considerations

This tool runs entirely in the browser and does not:
- Store any data persistently
- Send data to external servers
- Require network access beyond loading the page
- Handle sensitive information like actual keys or credentials

## License

This tool is part of the in-toto project and follows the same Apache 2.0 license.

## Support

For issues, questions, or contributions:
- File issues on the in-toto GitHub repository
- Join the in-toto community discussions
- Refer to the main in-toto documentation for integration details

---

**Note**: This tool provides planning and visualization capabilities. Actual in-toto implementation requires following the specific integration guides for your chosen CI/CD platform and installing the necessary in-toto components.
