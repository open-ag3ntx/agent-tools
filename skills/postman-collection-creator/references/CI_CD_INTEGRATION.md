# CI/CD Integration Guide

## Newman Installation
```bash
# Install globally
npm install -g newman

# Install with HTML reporter
npm install -g newman newman-reporter-html
```

## Basic Newman Commands
```bash
# Run collection with environment
newman run collection.json -e environment.json

# Run with data file
newman run collection.json -d test-data.csv

# Generate HTML report
newman run collection.json -r html --reporter-html-export report.html

# Run with timeout and bail on error
newman run collection.json \
  --timeout-request 10000 \
  --bail \
  --iteration-count 5
```

## GitHub Actions

**.github/workflows/api-tests.yml:**
```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Newman
        run: npm install -g newman newman-reporter-htmlextra
      
      - name: Run API Tests
        run: |
          newman run postman/collection.json \
            -e postman/environment.json \
            -r cli,htmlextra \
            --reporter-htmlextra-export reports/report.html
      
      - name: Upload Report
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: test-report
          path: reports/report.html
```

## Jenkins Pipeline

**Jenkinsfile:**
```groovy
pipeline {
    agent any
    
    stages {
        stage('Install Newman') {
            steps {
                sh 'npm install -g newman'
            }
        }
        
        stage('Run API Tests') {
            steps {
                sh '''
                    newman run collection.json \
                        -e ${ENVIRONMENT}.json \
                        -r junit,cli \
                        --reporter-junit-export results.xml
                '''
            }
        }
    }
    
    post {
        always {
            junit 'results.xml'
            archiveArtifacts artifacts: '*.xml', allowEmptyArchive: true
        }
    }
}
```

## GitLab CI

**.gitlab-ci.yml:**
```yaml
api-tests:
  image: postman/newman:alpine
  stage: test
  script:
    - newman run collection.json \
        -e environment.json \
        -r cli,junit \
        --reporter-junit-export report.xml
  artifacts:
    when: always
    reports:
      junit: report.xml
```

## Docker Integration

**Dockerfile:**
```dockerfile
FROM postman/newman:alpine

COPY postman /etc/newman

WORKDIR /etc/newman

CMD ["run", "collection.json", "-e", "environment.json"]
```

**Run with Docker:**
```bash
docker build -t api-tests .
docker run -t api-tests
```

## Environment Variables in CI
```bash
# Set environment variables
export BASE_URL="https://api.production.com"
export API_KEY="your-api-key"

# Run with env vars
newman run collection.json \
  --env-var "base_url=$BASE_URL" \
  --env-var "api_key=$API_KEY"
```

## Scheduled Monitoring

**cron schedule:**
```bash
# Run tests every hour
0 * * * * newman run /path/to/collection.json -e /path/to/env.json
```

## Slack Notifications
```bash
# Run and send notification
newman run collection.json \
  && curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"API tests passed!"}' \
  $SLACK_WEBHOOK_URL \
  || curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"API tests failed!"}' \
  $SLACK_WEBHOOK_URL
```