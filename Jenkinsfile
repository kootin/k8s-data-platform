// CI/CD for k8s-data-platform.
//
// CI (every build): lint Python / Terraform / Kubernetes manifests, unit tests,
//   and a warehouse-load integration test against a throwaway Postgres.
// CD (DEPLOY=true): build the Airflow image tagged with the commit, load it into
//   the kind cluster, roll it out, then run the DAG end to end as a smoke test.
//
// The cluster itself is created by Terraform (`make infra`); Jenkins deploys
// the application onto it. See README.md > "CI/CD with Jenkins".

pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    timeout(time: 45, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  parameters {
    booleanParam(name: 'DEPLOY', defaultValue: true, description: 'Build, deploy and smoke test on the kind cluster')
    string(name: 'SMOKE_DAY', defaultValue: '', description: 'Day for the smoke test (YYYY-MM-DD); blank = 3 days ago')
  }

  environment {
    CLUSTER_NAME = 'k8s-data-platform'
    NAMESPACE    = 'data-platform'
    KUBECONFIG   = "${WORKSPACE}/.kubeconfig"
    CI_POSTGRES  = "ci-postgres-${BUILD_NUMBER}"
  }

  stages {
    stage('Setup') {
      steps {
        script {
          env.IMAGE_TAG = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
        }
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install --quiet --upgrade pip
          pip install --quiet -r requirements-dev.txt
        '''
      }
    }

    stage('Lint') {
      parallel {
        stage('Python') {
          steps {
            sh '. .venv/bin/activate && ruff check . && ruff format --check .'
          }
        }
        stage('Terraform') {
          steps {
            dir('terraform') {
              sh '''
                terraform fmt -check -recursive
                terraform init -backend=false -input=false
                terraform validate
              '''
            }
          }
        }
        stage('Kubernetes manifests') {
          steps {
            sh 'mkdir -p reports && kubectl kustomize k8s > reports/rendered-manifests.yaml'
          }
        }
      }
    }

    stage('Tests') {
      steps {
        // Throwaway Postgres on the kind Docker network, reachable by name.
        sh 'docker run -d --rm --name "$CI_POSTGRES" --network kind -e POSTGRES_PASSWORD=postgres postgres:16-alpine'
        sh '''
          for i in $(seq 1 30); do
            docker exec "$CI_POSTGRES" pg_isready -U postgres >/dev/null 2>&1 && break
            sleep 2
          done
          . .venv/bin/activate
          TEST_DATABASE_URL="postgresql://postgres:postgres@${CI_POSTGRES}:5432/postgres" \
            pytest -q --junitxml=reports/junit.xml
        '''
      }
      post {
        always {
          junit 'reports/junit.xml'
          sh 'docker rm -f "$CI_POSTGRES" >/dev/null 2>&1 || true'
        }
      }
    }

    stage('Connect to cluster') {
      when { expression { params.DEPLOY } }
      steps {
        sh '''
          kind get clusters | grep -qx "$CLUSTER_NAME" \
            || { echo "kind cluster $CLUSTER_NAME not found: run 'make infra' first"; exit 1; }
          kind get kubeconfig --name "$CLUSTER_NAME" --internal > "$KUBECONFIG"
          kubectl get nodes
        '''
      }
    }

    stage('Build & load image') {
      when { expression { params.DEPLOY } }
      steps {
        sh 'scripts/build-image.sh'
      }
    }

    stage('Deploy') {
      when { expression { params.DEPLOY } }
      steps {
        sh 'scripts/deploy.sh'
      }
    }

    stage('Smoke test') {
      when { expression { params.DEPLOY } }
      steps {
        sh 'scripts/smoke-test.sh ${SMOKE_DAY}'
      }
    }
  }

  post {
    failure {
      script {
        if (params.DEPLOY && fileExists(env.KUBECONFIG)) {
          sh 'scripts/troubleshoot.sh > reports/troubleshoot.txt 2>&1 || true'
        }
      }
    }
    always {
      archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
    }
  }
}
